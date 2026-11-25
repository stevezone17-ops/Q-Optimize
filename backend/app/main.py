"""Main FastAPI application entry point for Q-Optimize."""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime, timezone

# Ensure project root is on sys.path so `backend.app.*` imports resolve
# regardless of whether uvicorn is invoked as `app.main:app` or `backend.app.main:app`.
_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.cors import configure_cors
from backend.app.core.logging import logger
from backend.app.core.middleware import (
    SecurityHeadersMiddleware,
    PayloadSizeLimitMiddleware,
    RateLimiterMiddleware,
)
from backend.app.db.mongodb import db_manager
from backend.app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown routines."""
    logger.info(
        f"Initializing {settings.PROJECT_NAME} v{settings.VERSION} "
        f"(env={settings.APP_ENV}, debug={settings.DEBUG})..."
    )
    # Attempt DB connection
    await db_manager.connect_to_database()
    db_status = await db_manager.get_db_status()
    logger.info(
        f"Persistence engine ready: {db_status.get('engine')} "
        f"(connected={db_status.get('connected')})"
    )
    # Seed default platform admin account if needed
    try:
        from backend.app.services.auth_service import AuthService
        await AuthService.seed_default_admin_if_needed()
    except Exception as e:
        logger.warning(f"Admin seeding warning: {e}")
    logger.info(f"API router mounted at '{settings.API_V1_PREFIX}' ({len(app.routes)} total routes). Startup complete.")
    yield
    # Shutdown
    logger.info("Shutting down Q-Optimize Backend Engine...")
    await db_manager.close_database_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Q-Optimize: AI-Assisted Hybrid Quantum-Classical Optimization Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
configure_cors(app)

# Attach Production Security Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PayloadSizeLimitMiddleware)
app.add_middleware(RateLimiterMiddleware)

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify request parameters."},
    )


# Root Health & Probe Endpoints (Convenience)
@app.get("/health", tags=["System"])
async def root_health() -> Dict[str, Any]:
    db_status = await db_manager.get_db_status()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
    }


@app.get("/health/live", tags=["System"])
async def root_liveness() -> Dict[str, Any]:
    return {"status": "live", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/health/ready", tags=["System"])
async def root_readiness(response: Response) -> Dict[str, Any]:
    db_status = await db_manager.get_db_status()
    is_ready = db_status.get("connected") is True or db_status.get("engine") == "in_memory_fallback"
    if not is_ready:
        response.status_code = 503
    return {
        "status": "ready" if is_ready else "not_ready",
        "database_connected": db_status.get("connected", False),
        "engine": db_status.get("engine"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }



# Include Versioned API Routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
