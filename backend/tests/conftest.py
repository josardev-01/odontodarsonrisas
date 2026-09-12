import os

os.environ["DAR_SONRISAS_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DAR_SONRISAS_AUTO_CREATE_SCHEMA"] = "true"
os.environ["DAR_SONRISAS_SEED_SYNTHETIC_PROFESSIONALS"] = "true"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client


@pytest_asyncio.fixture
def auth_headers():
    return {"X-Dev-User": "recepcion-ejemplo", "X-Dev-Role": "recepcion"}

