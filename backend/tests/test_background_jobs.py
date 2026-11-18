"""Tests for Background Job Reliability, Concurrency Control, Cancellation, and Timeouts (Stage 9.4)."""

import asyncio
import pytest
from fastapi import HTTPException
from backend.app.core.config import settings
from backend.app.workers.job_queue import (
    job_queue_manager,
    JobType,
    JobStatus,
    CancellationToken,
)


@pytest.fixture(autouse=True)
def reset_queue_state():
    """Reset manager state between tests."""
    job_queue_manager._jobs.clear()
    job_queue_manager._tokens.clear()
    job_queue_manager._dead_letter_queue.clear()
    job_queue_manager._active_tasks.clear()


@pytest.mark.asyncio
async def test_job_submission_and_successful_completion():
    """Verify job lifecycle from submission through completion."""
    async def sample_work(token: CancellationToken, val: int) -> int:
        await asyncio.sleep(0.05)
        return val * 2

    record = job_queue_manager.submit_job(
        user_id="user_123",
        job_type=JobType.GENERAL,
        work_coro_fn=sample_work,
        val=21,
    )
    assert record.status in [JobStatus.PENDING, JobStatus.RUNNING]

    # Await completion
    await asyncio.sleep(0.15)
    updated = job_queue_manager.get_job(record.job_id)
    assert updated.status == JobStatus.COMPLETED
    assert updated.result == 42
    assert updated.progress == 1.0


@pytest.mark.asyncio
async def test_user_concurrency_limit_exceeded():
    """Verify exceeding MAX_CONCURRENT_USER_JOBS rejects further submissions with 429."""
    async def slow_work(token: CancellationToken):
        await asyncio.sleep(1.0)

    # Submit up to max limit (3)
    for _ in range(settings.MAX_CONCURRENT_USER_JOBS):
        job_queue_manager.submit_job(
            user_id="monopolizing_user",
            job_type=JobType.GENERAL,
            work_coro_fn=slow_work,
        )

    # 4th submission must be rejected
    with pytest.raises(HTTPException) as exc_info:
        job_queue_manager.submit_job(
            user_id="monopolizing_user",
            job_type=JobType.GENERAL,
            work_coro_fn=slow_work,
        )
    assert exc_info.value.status_code == 429
    assert "concurrency limit exceeded" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_cooperative_job_cancellation():
    """Verify cooperative cancellation sets token flag and transitions job to CANCELLED."""
    cancelled_observed = False

    async def long_iterative_work(token: CancellationToken):
        nonlocal cancelled_observed
        for _ in range(20):
            token.check_cancelled()
            await asyncio.sleep(0.05)
        return "finished"

    record = job_queue_manager.submit_job(
        user_id="cancel_user",
        job_type=JobType.QUANTUM_QAOA,
        work_coro_fn=long_iterative_work,
    )

    await asyncio.sleep(0.05)
    # Trigger cancellation
    success = job_queue_manager.cancel_job(record.job_id, user_id="cancel_user")
    assert success is True

    await asyncio.sleep(0.1)
    updated = job_queue_manager.get_job(record.job_id)
    assert updated.status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_job_timeout_enforcement():
    """Verify jobs exceeding time_limit_seconds are marked TIMEOUT and moved to dead-letter queue."""
    async def runaway_simulation(token: CancellationToken):
        await asyncio.sleep(1.0)

    record = job_queue_manager.submit_job(
        user_id="timeout_user",
        job_type=JobType.QUANTUM_QAOA,
        work_coro_fn=runaway_simulation,
        time_limit_seconds=0.1,  # Short timeout
        max_retries=0,
    )

    await asyncio.sleep(0.25)
    updated = job_queue_manager.get_job(record.job_id)
    assert updated.status == JobStatus.TIMEOUT
    assert "timed out" in updated.error.lower()

    # Check dead-letter queue
    dlq = job_queue_manager.get_dead_letter_queue()
    assert any(j.job_id == record.job_id for j in dlq)


@pytest.mark.asyncio
async def test_job_transient_failure_and_retry():
    """Verify transient error triggers retry and succeeds on subsequent attempt."""
    attempts = 0

    async def flaky_work(token: CancellationToken):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Transient socket blip")
        return "success_on_retry"

    record = job_queue_manager.submit_job(
        user_id="retry_user",
        job_type=JobType.CLASSICAL_SOLVER,
        work_coro_fn=flaky_work,
        max_retries=2,
    )

    await asyncio.sleep(0.8)
    updated = job_queue_manager.get_job(record.job_id)
    assert updated.status == JobStatus.COMPLETED
    assert updated.result == "success_on_retry"
    assert updated.retry_count == 1


@pytest.mark.asyncio
async def test_permanent_failure_logged_to_dead_letter():
    """Verify unrecoverable job failure is captured in dead-letter queue."""
    async def doomed_task(token: CancellationToken):
        raise ValueError("Fatal invalid formulation data")

    record = job_queue_manager.submit_job(
        user_id="fail_user",
        job_type=JobType.GENERAL,
        work_coro_fn=doomed_task,
        max_retries=1,
    )

    await asyncio.sleep(0.8)
    updated = job_queue_manager.get_job(record.job_id)
    assert updated.status == JobStatus.FAILED
    assert "Fatal invalid" in updated.error

    dlq = job_queue_manager.get_dead_letter_queue()
    assert any(j.job_id == record.job_id for j in dlq)


@pytest.mark.asyncio
async def test_system_resource_guard_rejection():
    """Verify resource guard rejects dispatch when memory saturation threshold exceeded."""
    original_threshold = settings.MEMORY_SAFETY_THRESHOLD_PERCENT
    try:
        # Set threshold unrealistically low to trigger saturation guard
        settings.MEMORY_SAFETY_THRESHOLD_PERCENT = 0.01

        async def dummy_work(token: CancellationToken):
            return "done"

        with pytest.raises(HTTPException) as exc_info:
            job_queue_manager.submit_job(
                user_id="resource_user",
                job_type=JobType.QUANTUM_QAOA,
                work_coro_fn=dummy_work,
            )
        assert exc_info.value.status_code == 503
        assert "Compute cluster temporarily saturated" in exc_info.value.detail
    finally:
        settings.MEMORY_SAFETY_THRESHOLD_PERCENT = original_threshold

