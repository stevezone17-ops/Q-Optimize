"""Main FastAPI application entry point for Q-Optimize."""

from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import FastAPI, Request
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
    logger.info("Initializing Q-Optimize Backend Engine...")
    # Attempt DB connection
    await db_manager.connect_to_database()
    # Seed default platform admin account if needed
    try:
        from backend.app.services.auth_service import AuthService
        await AuthService.seed_default_admin_if_needed()
    except Exception as e:
        logger.warning(f"Admin seeding warning: {e}")
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


# Root Health Check (Convenience)
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


# Include Versioned API Routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
