"""API Security, Rate Limiting, Request Validation, and Header Enforcement Middleware."""

import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple, Any, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from backend.app.core.config import settings
from backend.app.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enforce production HTTP security headers on all responses according to
    OWASP and modern web standards.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "font-src 'self' data:; "
            "connect-src 'self' ws:; "
            "frame-ancestors 'none';"
        )
        return response


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Reject requests exceeding maximum permitted payload size (10 MB).
    Protects against memory starvation and DoS attacks.
    """

    MAX_PAYLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.MAX_PAYLOAD_BYTES:
                    logger.warning(
                        f"Payload size {content_length} bytes exceeded limit {self.MAX_PAYLOAD_BYTES} "
                        f"on {request.method} {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE
                        if hasattr(status, "HTTP_413_CONTENT_TOO_LARGE")
                        else 413,
                        content={"detail": "Request payload exceeds maximum allowable limit of 10MB."},
                    )
            except ValueError:
                pass
        return await call_next(request)


class InMemoryRateLimiter:
    """
    Sliding-window in-memory rate limiter per client IP / category.
    Configurable quotas:
      - 'auth': 20 requests / minute
      - 'solver': 45 requests / minute
      - 'general': 300 requests / minute
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._history: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self.quotas: Dict[str, int] = {
            "auth": 20,
            "solver": 45,
            "general": 300,
        }

    def reset(self) -> None:
        """Clear all rate limiting history (for test isolation)."""
        self._history.clear()

    def get_category(self, path: str) -> str:
        if path.startswith("/api/v1/auth"):
            return "auth"
        if path.startswith("/api/v1/solvers") or path.startswith("/api/v1/experiments"):
            return "solver"
        return "general"

    def is_allowed(self, client_ip: str, path: str) -> Tuple[bool, int]:
        if not self.enabled:
            return True, 0

        category = self.get_category(path)
        limit = self.quotas.get(category, 300)
        now = time.time()
        window = 60.0  # 1 minute sliding window

        key = (client_ip, category)
        dq = self._history[key]

        # Purge timestamps outside the 60s sliding window
        while dq and dq[0] <= now - window:
            dq.popleft()

        if len(dq) >= limit:
            return False, int(window - (now - dq[0]))

        dq.append(now)
        return True, 0


rate_limiter = InMemoryRateLimiter(enabled=True)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware delegating to sliding window rate limiter."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine client identifier
        client_ip = request.client.host if request.client else "127.0.0.1"
        # Forwarded header support for reverse proxy
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        allowed, retry_after = rate_limiter.is_allowed(client_ip, request.url.path)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(max(1, retry_after))},
                content={
                    "detail": (
                        f"Rate limit exceeded for this endpoint category. "
                        f"Please retry after {max(1, retry_after)} seconds."
                    )
                },
            )
        return await call_next(request)


def sanitize_query_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize query and filter dictionary keys.
    Rejects NoSQL injection keys starting with '$' or containing '.'
    """
    for key, value in params.items():
        if key.startswith("$") or "." in key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parameter key '{key}'. Special operator keys are prohibited.",
            )
        if isinstance(value, dict):
            sanitize_query_parameters(value)
    return params


def enforce_quantum_quotas(
    num_qubits: int,
    p_depth: int,
    max_evaluations: Optional[int] = None,
) -> None:
    """
    Strict platform resource quota enforcement.
    Prevents simulation memory overflow and compute starvation.
    """
    MAX_QUBITS = 20
    MAX_DEPTH = 10
    MAX_EVALUATIONS = 500

    if num_qubits > MAX_QUBITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Quantum simulation quota exceeded: Problem requires {num_qubits} qubits, "
                f"exceeding the platform statevector limit of {MAX_QUBITS} qubits."
            ),
        )

    if p_depth > MAX_DEPTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"QAOA depth quota exceeded: requested p={p_depth}, max allowable is {MAX_DEPTH}.",
        )

    if max_evaluations and max_evaluations > MAX_EVALUATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Optimizer evaluation budget exceeded: requested {max_evaluations}, "
                f"maximum allowable limit is {MAX_EVALUATIONS}."
            ),
        )

