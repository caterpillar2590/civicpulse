from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

_engine_kwargs = {"pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs["pool_size"] = 10

engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def db_is_ready() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    """Called on SIGTERM shutdown so the connection pool closes cleanly."""
    await engine.dispose()
