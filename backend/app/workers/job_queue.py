"""Centralized Job Queue Manager with Concurrency Limits, Timeouts, Retries, and Cancellation."""

import uuid
import time
import asyncio
import traceback
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Coroutine, Tuple
from datetime import datetime, timezone
import psutil
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from backend.app.core.config import settings
from backend.app.core.logging import logger


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobType(str, Enum):
    QUANTUM_QAOA = "quantum_qaoa"
    CLASSICAL_SOLVER = "classical_solver"
    BENCHMARK_EXPERIMENT = "benchmark_experiment"
    GENERAL = "general"


class JobCancelledError(Exception):
    """Raised when job is cooperatively aborted by user cancellation."""
    pass


class CancellationToken:
    """Thread-safe cooperative cancellation token for long-running routines."""

    def __init__(self):
        self._is_cancelled = False

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def cancel(self) -> None:
        self._is_cancelled = True

    def check_cancelled(self) -> None:
        if self._is_cancelled:
            raise JobCancelledError("Job execution aborted by user cancellation request.")


class JobRecord(BaseModel):
    """Structured representation of a queued or executed background job."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_limit_seconds: float = 120.0
    retry_count: int = 0
    max_retries: int = 2
    result: Optional[Any] = None
    error: Optional[str] = None
    cancellation_requested: bool = False

    class Config:
        arbitrary_types_allowed = True


class JobQueueManager:
    """Enterprise job queue enforcing concurrency ceilings, timeouts, and resource limits."""

    def __init__(self):
        self._jobs: Dict[str, JobRecord] = {}
        self._tokens: Dict[str, CancellationToken] = {}
        self._dead_letter_queue: List[JobRecord] = []
        self._active_tasks: Dict[str, asyncio.Task] = {}

    def check_system_resources(self) -> Tuple[bool, str]:
        """Verify host CPU and RAM are within safe operational thresholds before heavy dispatch."""
        if not settings.ENABLE_RESOURCE_GUARD:
            return True, "Resource guard disabled"

        try:
            mem = psutil.virtual_memory()
            if mem.percent > settings.MEMORY_SAFETY_THRESHOLD_PERCENT:
                return False, f"Host memory saturation ({mem.percent}% > {settings.MEMORY_SAFETY_THRESHOLD_PERCENT}% threshold)"
            return True, "Resources healthy"
        except Exception as e:
            logger.warning(f"Resource check check failed: {e}")
            return True, "Resource check skipped"

    def get_user_active_count(self, user_id: str) -> int:
        return sum(
            1 for j in self._jobs.values()
            if j.user_id == user_id and j.status in [JobStatus.PENDING, JobStatus.RUNNING]
        )

    def get_type_active_count(self, job_type: JobType) -> int:
        return sum(
            1 for j in self._jobs.values()
            if j.job_type == job_type and j.status in [JobStatus.PENDING, JobStatus.RUNNING]
        )

    def submit_job(
        self,
        user_id: str,
        job_type: JobType,
        work_coro_fn: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        time_limit_seconds: float = 120.0,
        max_retries: int = 1,
        **kwargs,
    ) -> JobRecord:
        """Enforce concurrency limits, pre-checks, and register job."""
        # 1. User concurrency limit
        if self.get_user_active_count(user_id) >= settings.MAX_CONCURRENT_USER_JOBS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"User concurrency limit exceeded. Maximum {settings.MAX_CONCURRENT_USER_JOBS} active jobs permitted.",
            )

        # 2. Solver type concurrency limit
        limit = (
            settings.MAX_CONCURRENT_SIMULATIONS
            if job_type == JobType.QUANTUM_QAOA
            else settings.MAX_CONCURRENT_CLASSICAL_JOBS
        )
        if self.get_type_active_count(job_type) >= limit:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Platform is currently at maximum simulation capacity for {job_type.value}. Please retry shortly.",
            )

        # 3. System resource pre-check
        is_safe, reason = self.check_system_resources()
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Compute cluster temporarily saturated: {reason}. Please wait for active workloads to finish.",
            )

        job_id = str(uuid.uuid4())
        record = JobRecord(
            job_id=job_id,
            user_id=user_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            time_limit_seconds=time_limit_seconds,
            max_retries=max_retries,
        )
        token = CancellationToken()
        self._jobs[job_id] = record
        self._tokens[job_id] = token

        # Dispatch execution wrapper
        task = asyncio.create_task(
            self._execute_job_lifecycle(job_id, work_coro_fn, token, *args, **kwargs)
        )
        self._active_tasks[job_id] = task

        logger.info(f"Dispatched background job {job_id} [{job_type.value}] for user {user_id}")
        return record

    async def _execute_job_lifecycle(
        self,
        job_id: str,
        work_coro_fn: Callable[..., Coroutine[Any, Any, Any]],
        token: CancellationToken,
        *args,
        **kwargs,
    ) -> None:
        """Manages job execution, timeout watchdog, cooperative cancellation, and retries."""
        record = self._jobs[job_id]
        record.status = JobStatus.RUNNING
        record.started_at = datetime.now(timezone.utc)

        attempts = 0
        while attempts <= record.max_retries:
            attempts += 1
            record.retry_count = attempts - 1
            try:
                # Execute with timeout watchdog
                result = await asyncio.wait_for(
                    work_coro_fn(token, *args, **kwargs),
                    timeout=record.time_limit_seconds,
                )
                record.status = JobStatus.COMPLETED
                record.progress = 1.0
                record.result = result
                record.completed_at = datetime.now(timezone.utc)
                logger.info(f"Job {job_id} completed successfully.")
                return

            except asyncio.TimeoutError:
                record.status = JobStatus.TIMEOUT
                record.error = f"Job timed out after exceeding allocation of {record.time_limit_seconds}s."
                record.completed_at = datetime.now(timezone.utc)
                self._dead_letter_queue.append(record)
                logger.warning(f"Job {job_id} timed out.")
                return

            except JobCancelledError:
                record.status = JobStatus.CANCELLED
                record.error = "Job cancelled by client request."
                record.completed_at = datetime.now(timezone.utc)
                logger.info(f"Job {job_id} successfully cancelled.")
                return

            except Exception as exc:
                err_str = f"{type(exc).__name__}: {str(exc)}"
                logger.warning(f"Job {job_id} error on attempt {attempts}/{record.max_retries + 1}: {err_str}")
                if attempts <= record.max_retries and not token.is_cancelled:
                    await asyncio.sleep(0.5 * attempts)
                    continue
                else:
                    record.status = JobStatus.FAILED
                    record.error = err_str
                    record.completed_at = datetime.now(timezone.utc)
                    self._dead_letter_queue.append(record)
                    logger.error(f"Job {job_id} failed permanently: {err_str}\n{traceback.format_exc()}")
                    return

    def cancel_job(self, job_id: str, user_id: str, is_admin: bool = False) -> bool:
        """Cancel a pending or running job cooperatively."""
        record = self._jobs.get(job_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found.",
            )

        if not is_admin and record.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to cancel this job.",
            )

        if record.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT]:
            return False

        token = self._tokens.get(job_id)
        if token:
            token.cancel()
        record.cancellation_requested = True
        record.status = JobStatus.CANCELLED
        record.completed_at = datetime.now(timezone.utc)
        record.error = "Job cancelled by user."

        task = self._active_tasks.get(job_id)
        if task and not task.done():
            task.cancel()

        logger.info(f"Cancellation enforced on job {job_id}")
        return True

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def list_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
    ) -> List[JobRecord]:
        results = list(self._jobs.values())
        if user_id:
            results = [j for j in results if j.user_id == user_id]
        if status:
            results = [j for j in results if j.status == status]
        return sorted(results, key=lambda j: j.created_at, reverse=True)

    def get_dead_letter_queue(self) -> List[JobRecord]:
        return self._dead_letter_queue


job_queue_manager = JobQueueManager()

