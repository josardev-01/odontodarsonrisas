import os

os.environ["DAR_SONRISAS_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DAR_SONRISAS_AUTO_CREATE_SCHEMA"] = "true"
os.environ["DAR_SONRISAS_SEED_SYNTHETIC_PROFESSIONALS"] = "true"
os.environ["DAR_SONRISAS_BOOTSTRAP_TOKEN"] = "synthetic-bootstrap-token-for-tests"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client


@pytest_asyncio.fixture
async def auth_headers(client):
    payload = {
        "bootstrap_token": "synthetic-bootstrap-token-for-tests",
        "email": "admin@example.com",
        "display_name": "Admin Sintetico",
        "password": "synthetic-password-only-for-tests",
    }
    response = await client.post("/api/v1/auth/bootstrap", json=payload)
    if response.status_code == 409:
        response = await client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert response.status_code in (200, 201), response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}
