"""
API-level tests using FastAPI's ASGI transport directly against the app,
covering session creation, retrieval, and the health check contract.
Requires the db container to be running (same DATABASE_URL as .env).
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_check_reports_all_subsystems():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "database" in body
    assert "ollama" in body
    assert "vector_index" in body


@pytest.mark.asyncio
async def test_create_session_returns_valid_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/sessions", json={"title": "pytest session"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "pytest session"
    assert "id" in body


@pytest.mark.asyncio
async def test_get_nonexistent_session_returns_404():
    transport = ASGITransport(app=app)
    fake_id = "00000000-0000-0000-0000-000000000000"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/sessions/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_messages_after_creation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post("/api/sessions", json={"title": "history test"})
        session_id = created.json()["id"]

        history = await client.get(f"/api/sessions/{session_id}")

    assert history.status_code == 200
    assert history.json() == []  # no messages sent yet