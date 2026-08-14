"""Security Middleware & Rate Limiting Utility."""

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware injecting modern security HTTP headers on all API responses."""

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self';"
        )
        response.headers["Server"] = "ALI-Agent-API"
        return response


class RateLimiter:
    """In-memory sliding window rate limiter for brute-force prevention.

    Note: This in-memory rate limiter is designed for single-process deployments.
    Distributed multi-instance production deployments must use a shared storage
    backend such as Redis.
    """

    def __init__(self, max_requests: int = 20, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, key: str) -> None:
        """Enforce rate limit for specified key (e.g. IP or username)."""
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = [t for t in self._requests[key] if t > window_start]
        self._requests[key] = timestamps

        if len(timestamps) >= self.max_requests:
            msg = f"Rate limit exceeded: Max {self.max_requests} req / {self.window_seconds}s"
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=msg,
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[key].append(now)


# Global Rate Limiter Instances
login_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
agent_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
