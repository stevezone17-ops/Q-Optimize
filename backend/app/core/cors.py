"""CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings


def configure_cors(app: FastAPI) -> None:
    origins = settings.FRONTEND_ORIGIN
    if isinstance(origins, str):
        origins = [origins]

    # Security: Ensure origins do not use wildcard '*' when allow_credentials is True
    sanitized_origins = [o for o in origins if o != "*"]
    if not sanitized_origins:
        sanitized_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=sanitized_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    )
