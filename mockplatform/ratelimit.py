from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> float | None:
        now = self.clock()
        window = self.hits[key]
        while window and now - window[0] >= self.window_seconds:
            window.popleft()
        if len(window) >= self.limit:
            return self.window_seconds - (now - window[0])
        window.append(now)
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: SlidingWindowLimiter) -> None:
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/openapi.json", "/docs"):
            return await call_next(request)
        key = request.headers.get("x-api-key") or (request.client.host if request.client else "anonymous")
        retry_after = self.limiter.check(key)
        if retry_after is not None:
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
            )
        return await call_next(request)
