"""Job status, queue inspection, and cancellation endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.api.deps import get_current_user, require_role
from backend.app.domain.auth.models import User, UserRole
from backend.app.workers.job_queue import (
    job_queue_manager,
    JobRecord,
    JobStatus,
)

router = APIRouter(prefix="/jobs", tags=["Background Jobs & Concurrency"])


@router.get("", response_model=List[JobRecord])
async def list_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
) -> List[JobRecord]:
    """List jobs for the authenticated user (or all jobs if admin)."""
    if current_user.role == UserRole.ADMIN:
        return job_queue_manager.list_jobs(user_id=None, status=status_filter)
    return job_queue_manager.list_jobs(user_id=current_user.id, status=status_filter)


@router.get("/dead-letter", response_model=List[JobRecord])
async def list_dead_letter_queue(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.RESEARCHER])),
) -> List[JobRecord]:
    """Inspect dead-letter queue for failed or timed-out solver executions."""
    return job_queue_manager.get_dead_letter_queue()


@router.get("/{job_id}", response_model=JobRecord)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> JobRecord:
    """Retrieve execution status, progress, and results for a background job."""
    job = job_queue_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    if current_user.role != UserRole.ADMIN and job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this job record.",
        )
    return job


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Cancel a running or queued background job."""
    is_admin = current_user.role == UserRole.ADMIN
    cancelled = job_queue_manager.cancel_job(job_id, user_id=current_user.id, is_admin=is_admin)
    return {
        "job_id": job_id,
        "cancelled": cancelled,
        "detail": "Cancellation signal dispatched to worker." if cancelled else "Job already finished.",
    }

