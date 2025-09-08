"""Custom FastAPI middleware components."""
from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    header_name = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        cid = request.headers.get(self.header_name, str(uuid.uuid4()))
        request.state.correlation_id = cid
        response: Response = await call_next(request)
        response.headers[self.header_name] = cid
        return response
