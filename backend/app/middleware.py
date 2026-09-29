from __future__ import annotations

import time
import uuid

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_config import request_id_ctx

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "Request latency", ["method", "path"])
TRIAGE_LATENCY = Histogram("triage_latency_seconds", "Triage call latency")
TRIAGE_FALLBACK_COUNT = Counter("triage_fallback_total", "Times triage fell back to rules")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(incoming_id)
        start = time.monotonic()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        elapsed = time.monotonic() - start
        path = request.url.path
        REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
        response.headers["X-Request-ID"] = incoming_id
        return response
