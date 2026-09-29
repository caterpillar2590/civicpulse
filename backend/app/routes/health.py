from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.db import db_is_ready
from app.redis_client import redis_is_ready

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    # Liveness: process is alive. Must NOT touch the database - a slow DB
    # must never cause Kubernetes to restart the pod.
    return {"status": "alive"}


@router.get("/ready")
async def ready(response: Response):
    db_ok = await db_is_ready()
    redis_ok = await redis_is_ready()

    if db_ok and redis_ok:
        return {"status": "ready", "database": "ok", "cache": "ok"}

    response.status_code = 503
    failed = []
    if not db_ok:
        failed.append("database")
    if not redis_ok:
        failed.append("cache")
    return {"status": "not_ready", "failed_dependencies": failed}


@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
