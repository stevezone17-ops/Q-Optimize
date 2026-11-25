"""Health check endpoints with Kubernetes-compatible liveness and readiness probes."""

from typing import Dict, Any
from datetime import datetime, timezone
import psutil
from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from backend.app.db.mongodb import db_manager
from backend.app.workers.job_queue import job_queue_manager

router = APIRouter(tags=["System Health & Observability"])


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Return health status of API, version, environment, and database connectivity."""
    degraded_reasons = []

    try:
        db_status = await db_manager.get_db_status()
    except Exception as exc:
        db_status = {"connected": False, "engine": "unavailable", "error": str(exc)}
        degraded_reasons.append(f"database_error: {exc}")

    try:
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        cpu_percent = psutil.cpu_percent(interval=None)
    except Exception as exc:
        memory_percent = None
        cpu_percent = None
        degraded_reasons.append(f"telemetry_unavailable: {exc}")

    is_safe, resource_reason = job_queue_manager.check_system_resources()
    if not is_safe:
        degraded_reasons.append(f"resource_pressure: {resource_reason}")

    if not db_status.get("connected") and db_status.get("engine") != "in_memory_fallback":
        degraded_reasons.append("persistence_unavailable")

    active_jobs = len(job_queue_manager.list_jobs(status=None))
    dead_letters = len(job_queue_manager.get_dead_letter_queue())

    overall_status = "degraded" if degraded_reasons else "healthy"

    return {
        "status": overall_status,
        "degraded_reasons": degraded_reasons,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "phase": "Phase 10 - Production Ready & Research Validated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "workers": {
            "total_tracked_jobs": active_jobs,
            "dead_letter_count": dead_letters,
            "max_concurrent_simulations": settings.MAX_CONCURRENT_SIMULATIONS,
            "max_concurrent_classical": settings.MAX_CONCURRENT_CLASSICAL_JOBS,
        },
        "system": {
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
        },
        "supported_problems": ["max_cut", "assignment", "tsp"],
    }


@router.get("/health/live")
async def liveness_probe() -> Dict[str, Any]:
    """
    Kubernetes liveness probe.
    Returns HTTP 200 immediately if process event loop is alive.
    """
    return {
        "status": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
    }

@router.get("/health/ready")
async def readiness_probe(response: Response) -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    Verifies database connectivity and compute availability before routing client traffic.
    """
    db_status = await db_manager.get_db_status()
    is_safe, reason = job_queue_manager.check_system_resources()

    # Determine readiness
    is_ready = is_safe and (
        db_status.get("connected") is True
        or db_status.get("engine") == "in_memory_fallback"
    )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": db_status.get("connected", False),
        "engine": db_status.get("engine"),
        "resource_health": reason,
        "service": settings.PROJECT_NAME,
    }
