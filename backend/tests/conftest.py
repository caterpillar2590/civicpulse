import os

os.environ.setdefault("TRIAGE_PROVIDER", "simulated")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")  # isolated DB, never prod's

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.complaint import Base
import app.db as db_module
from app.redis_client import redis_client


@pytest_asyncio.fixture(autouse=True)
async def clean_redis():
    """Every test starts with an empty Redis DB 15. We also force the
    connection pool to reconnect lazily on THIS test's event loop: each
    pytest-asyncio test gets its own loop, and asyncio sockets opened on a
    previous loop break when reused ('attached to a different loop')."""
    await redis_client.connection_pool.disconnect()
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()
    await redis_client.connection_pool.disconnect()


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine, monkeypatch):
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with TestSession() as session:
            yield session

    from app.main import app as fastapi_app
    from app.db import get_db

    fastapi_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
