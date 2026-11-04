"""Health check endpoints."""

from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.db.mongodb import db_manager

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any], tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Return health status of API, version, environment, and database connectivity."""
    db_status = await db_manager.get_db_status()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "phase": "Phase 1 - Complete Platform Foundation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "supported_problems": ["max_cut", "assignment", "tsp"],
    }
