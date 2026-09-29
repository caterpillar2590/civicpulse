from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import dispose_engine
from app.logging_config import configure_logging
from app.middleware import ObservabilityMiddleware
from app.redis_client import close_redis
from app.routes import complaints, health, meta, stats

configure_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup complete")
    yield
    # SIGTERM handling: Uvicorn/Gunicorn already stop accepting new
    # connections and drain in-flight requests before lifespan shutdown
    # runs (given a sane --timeout-graceful-shutdown). We use this hook to
    # close the DB pool and Redis client cleanly so a rolling update never
    # leaves dangling connections on the old pod.
    logger.info("shutting down: draining connections")
    await dispose_engine()
    await close_redis()
    logger.info("shutdown complete")


app = FastAPI(title="CivicPulse API", version="1.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": "Validation failed", "errors": errors})


app.include_router(health.router)
app.include_router(complaints.router)
app.include_router(stats.router)
app.include_router(meta.router)
