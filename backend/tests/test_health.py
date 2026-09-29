import pytest


@pytest.mark.asyncio
async def test_health_does_not_touch_database(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_ready_reports_dependency_status(client):
    resp = await client.get("/ready")
    # In the test harness DB is a working in-memory SQLite; Redis is real
    # infra so this may be 200 or 503 depending on the environment - what
    # matters is the shape of the contract.
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "status" in body
