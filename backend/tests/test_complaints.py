import pytest


@pytest.mark.asyncio
async def test_submit_complaint_returns_201_with_triage_result(client):
    resp = await client.post(
        "/api/complaints",
        json={
            "text": "Burst water main flooding Street 12 since fajr",
            "location": "Street 12, G-9",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["category"] in ["water", "electricity", "sanitation", "roads", "streetlights", "other"]
    assert body["status"] == "open"
    assert body["triaged_by"] == "llm:simulated"
    assert len(body["ai_summary"]) <= 140


@pytest.mark.asyncio
async def test_submit_complaint_rejects_short_text_with_400(client):
    resp = await client.post("/api/complaints", json={"text": "too short", "location": "Street 1"})
    assert resp.status_code == 400
    body = resp.json()
    assert any(e["field"] == "text" for e in body["errors"])


@pytest.mark.asyncio
async def test_get_complaint_404_for_unknown_id(client):
    resp = await client.get("/api/complaints/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_status_transition_state_machine(client):
    create = await client.post(
        "/api/complaints",
        json={"text": "Streetlight has been broken for three weeks now", "location": "Street 9"},
    )
    complaint_id = create.json()["id"]

    # open -> in_progress: valid
    ok = await client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "in_progress"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "in_progress"

    # in_progress -> open: invalid, must be 409 naming the attempted transition
    bad = await client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "open"})
    assert bad.status_code == 409
    assert "in_progress" in bad.json()["detail"]
    assert "open" in bad.json()["detail"]


@pytest.mark.asyncio
async def test_stats_endpoint_reports_cache_header(client):
    await client.post(
        "/api/complaints",
        json={"text": "Garbage collection has not happened in two weeks", "location": "Sector I-8"},
    )
    first = await client.get("/api/stats")
    assert first.status_code == 200
    assert first.headers["X-Cache"] == "MISS"  # invalidated by the write above

    second = await client.get("/api/stats")
    assert second.headers["X-Cache"] == "HIT"


@pytest.mark.asyncio
async def test_rate_limiter_returns_429_with_retry_after(client, monkeypatch):
    from app import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "2")
    config.get_settings.cache_clear()

    payload = {"text": "Pothole growing bigger every day on main road", "location": "Main Road"}
    r1 = await client.post("/api/complaints", json=payload)
    r2 = await client.post("/api/complaints", json=payload)
    r3 = await client.post("/api/complaints", json=payload)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers

    config.get_settings.cache_clear()
