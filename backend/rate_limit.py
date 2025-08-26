"""Token bucket rate limiting middleware with optional Redis backend.

Falls back to in-memory bucket (single-process only) if REDIS not configured.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Optional
import os
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except ImportError:  # pragma: no cover
    redis = None  # type: ignore


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Optional Redis-backed rate limiter.

    Redis implementation uses Lua script for atomic refill + decrement.
    """

    LUA_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local capacity = tonumber(ARGV[2])
    local refill_rate = tonumber(ARGV[3])
    local ttl = tonumber(ARGV[4])
    local bucket = redis.call('HMGET', key, 'tokens', 'ts')
    local tokens = tonumber(bucket[1])
    local ts = tonumber(bucket[2])
    if tokens == nil then
        tokens = capacity
        ts = now
    end
    if now > ts then
        local delta = now - ts
        tokens = math.min(capacity, tokens + delta * refill_rate)
        ts = now
    end
    if tokens < 1 then
        redis.call('HMSET', key, 'tokens', tokens, 'ts', ts)
        redis.call('EXPIRE', key, ttl)
        return 0
    else
        tokens = tokens - 1
        redis.call('HMSET', key, 'tokens', tokens, 'ts', ts)
        redis.call('EXPIRE', key, ttl)
        return 1
    end
    """

    def __init__(self, app, limit_per_minute: int = 120, redis_url: str | None = None):  # type: ignore[override]
        super().__init__(app)
        self.capacity = max(1, limit_per_minute)
        self.refill_rate = self.capacity / 60.0
        self.tokens: Dict[str, float] = defaultdict(lambda: float(self.capacity))
        self.timestamp: Dict[str, float] = defaultdict(lambda: time.time())
        self._redis = None
        self._script_sha: Optional[str] = None
        if redis and redis_url:
            try:  # pragma: no cover
                self._redis = redis.Redis.from_url(redis_url, decode_responses=False)
                self._script_sha = self._redis.script_load(self.LUA_SCRIPT)
            except Exception:  # noqa: BLE001
                self._redis = None

    def _redis_allow(self, key: str) -> bool:
        if not self._redis or not self._script_sha:
            return False
        now = int(time.time())
        try:  # pragma: no cover
            allowed = self._redis.evalsha(
                self._script_sha,
                1,
                f"ratelimit:{key}",
                now,
                self.capacity,
                self.refill_rate,
                120,
            )
            return allowed == 1
        except Exception:  # noqa: BLE001
            return False

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        key = request.client.host if request.client else "global"
        limit = self.capacity
        remaining = None
        reset = int(time.time()) + 60
        if self._redis:
            allowed = self._redis_allow(key)
            if not allowed:
                headers = {
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                }
                raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=headers)
            # Can't cheaply compute remaining without extra roundtrip; omit or set -1 sentinel
            response = await call_next(request)
            response.headers.setdefault("X-RateLimit-Limit", str(limit))
            response.headers.setdefault("X-RateLimit-Remaining", "-1")
            response.headers.setdefault("X-RateLimit-Reset", str(reset))
            return response
        # Fallback in-memory
        now = time.time()
        last = self.timestamp[key]
        delta = now - last
        if delta > 0:
            new_tokens = self.tokens[key] + delta * self.refill_rate
            self.tokens[key] = min(self.capacity, new_tokens)
            self.timestamp[key] = now
        if self.tokens[key] < 1:
            headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset),
            }
            raise HTTPException(status_code=429, detail="Rate limit exceeded", headers=headers)
        self.tokens[key] -= 1
        remaining = int(self.tokens[key])
        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, remaining)))
        response.headers.setdefault("X-RateLimit-Reset", str(reset))
        return response