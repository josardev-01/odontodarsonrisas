import pytest


@pytest.mark.asyncio
async def test_admin_can_review_audit_events(client, auth_headers):
    response = await client.get("/api/v1/admin/audit-events?limit=10", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()
    assert {"actor_id","action","resource_type","outcome","occurred_at"}.issubset(response.json()[0])


@pytest.mark.asyncio
async def test_reception_cannot_review_audit_events(client, auth_headers):
    created = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={"email":"audit-reception@example.com","display_name":"Recepcion Auditoria","password":"synthetic-audit-password","role":"recepcion"},
    )
    assert created.status_code == 201
    login = await client.post("/api/v1/auth/login", json={"email":"audit-reception@example.com","password":"synthetic-audit-password"})
    response = await client.get("/api/v1/admin/audit-events", headers={"X-CSRF-Token":login.json()["csrf_token"]})
    assert response.status_code == 403
