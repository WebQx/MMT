"""Rate limiting middleware with optional Redis backend.

Adds response headers:
 - X-RateLimit-Limit
 - X-RateLimit-Remaining
 - X-RateLimit-Reset (epoch seconds bucket reset)
"""
from __future__ import annotations

import time
import hashlib
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import threading

try:
	import redis  # type: ignore
except Exception:  # pragma: no cover
	redis = None  # type: ignore


class _InMemoryBucket:
	def __init__(self, capacity: int, window_seconds: int = 60):
		self.capacity = capacity
		self.window = window_seconds
		self.tokens = capacity
		self.reset_at = int(time.time()) + window_seconds
		self.lock = threading.Lock()

	def take(self) -> tuple[bool, int, int]:
		now = int(time.time())
		with self.lock:
			if now >= self.reset_at:
				self.tokens = self.capacity
				self.reset_at = now + self.window
			allowed = self.tokens > 0
			if allowed:
				self.tokens -= 1
			return allowed, self.tokens, self.reset_at


_buckets: dict[str, _InMemoryBucket] = {}
_global_lock = threading.Lock()


class RateLimitMiddleware(BaseHTTPMiddleware):
	def __init__(self, app, limit_per_minute: int = 60, redis_url: Optional[str] = None):  # type: ignore[override]
		super().__init__(app)
		self.limit = limit_per_minute
		self.redis_url = redis_url
		self._r = None
		if redis_url and redis:
			try:
				self._r = redis.from_url(redis_url)
			except Exception:
				self._r = None

	async def dispatch(self, request: Request, call_next):  # type: ignore[override]
		if self.limit <= 0:
			return await call_next(request)
		key = self._key_for(request)
		allowed, remaining, reset_at = self._consume(key)
		if not allowed:
			return JSONResponse(status_code=429, content={"error": {"code": 429, "message": "Rate limit exceeded"}, "correlation_id": getattr(request.state,'correlation_id',None)})
		response: Response = await call_next(request)
		response.headers['X-RateLimit-Limit'] = str(self.limit)
		response.headers['X-RateLimit-Remaining'] = str(remaining)
		response.headers['X-RateLimit-Reset'] = str(reset_at)
		return response

	def _key_for(self, request: Request) -> str:
		ident = request.client.host if request.client else 'anon'
		raw = f"{ident}:{int(time.time()//60)}"
		return hashlib.sha256(raw.encode()).hexdigest()

	def _consume(self, key: str) -> tuple[bool, int, int]:
		# Redis path simple counter with expiration aligning to window boundary
		if self._r:
			try:
				pipe = self._r.pipeline()
				pipe.incr(key, 1)
				pipe.ttl(key)
				current, ttl = pipe.execute()
				if ttl == -1:
					# set expiry to next minute boundary
					now = int(time.time())
					reset_at = (now - (now % 60)) + 60
					self._r.expireat(key, reset_at)
					ttl = reset_at - now
				else:
					now = int(time.time())
					reset_at = now + ttl if ttl > 0 else now + 60
				remaining = max(0, self.limit - int(current))
				return (current <= self.limit, remaining, reset_at)
			except (redis.RedisError, ConnectionError, ValueError) as e:
				import structlog
				structlog.get_logger(__name__).warning("redis_rate_limit_failed", error=str(e))
		# In-memory path
		bucket_key = key
		with _global_lock:
			bucket = _buckets.get(bucket_key)
			if not bucket:
				bucket = _InMemoryBucket(self.limit)
				_buckets[bucket_key] = bucket
		allowed, remaining, reset_at = bucket.take()
		return allowed, remaining, reset_at
