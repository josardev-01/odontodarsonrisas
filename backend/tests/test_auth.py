import pytest
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.platform.database import SessionFactory


@pytest.mark.asyncio
async def test_bootstrap_login_me_csrf_and_logout(client, auth_headers):
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["roles"] == ["admin"]

    missing_csrf = await client.post("/api/v1/patients", json={})
    assert missing_csrf.status_code == 403

    logout = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_failed_login_is_generic_and_audited(client, auth_headers):
    response = await client.post("/api/v1/auth/login", json={"email": "missing@example.com", "password": "not-the-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    async with SessionFactory() as session:
        event = await session.scalar(select(AuditEvent).where(AuditEvent.action == "auth.login_failed").order_by(AuditEvent.occurred_at.desc()))
        assert event is not None
        assert event.detail is None


@pytest.mark.asyncio
async def test_admin_can_create_staff_but_not_patient_portal_user(client, auth_headers):
    staff = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={
            "email": "recepcion@example.com",
            "display_name": "Recepcion Sintetica",
            "password": "synthetic-password-only-for-tests",
            "role": "recepcion",
        },
    )
    assert staff.status_code == 201, staff.text
    assert staff.json()["roles"] == ["recepcion"]

    patient = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={
            "email": "portal@example.com",
            "display_name": "Portal Diferido",
            "password": "synthetic-password-only-for-tests",
            "role": "paciente",
        },
    )
    assert patient.status_code == 422


@pytest.mark.asyncio
async def test_admin_lists_updates_and_resets_staff_access(client, auth_headers):
    created = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={"email":"staff-management@example.com","display_name":"Staff Gestion","password":"synthetic-original-password","role":"recepcion"},
    )
    assert created.status_code == 201
    user_id = created.json()["id"]
    listed = await client.get("/api/v1/auth/users", headers=auth_headers)
    assert listed.status_code == 200
    assert user_id in {item["id"] for item in listed.json()}

    changed = await client.patch(
        f"/api/v1/auth/users/{user_id}",
        headers=auth_headers,
        json={"display_name":"Profesional Gestion","role":"profesional"},
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "profesional"

    reset = await client.post(
        f"/api/v1/auth/users/{user_id}/password",
        headers=auth_headers,
        json={"password":"synthetic-replacement-password"},
    )
    assert reset.status_code == 204
    old_login = await client.post("/api/v1/auth/login", json={"email":"staff-management@example.com","password":"synthetic-original-password"})
    assert old_login.status_code == 401
    new_login = await client.post("/api/v1/auth/login", json={"email":"staff-management@example.com","password":"synthetic-replacement-password"})
    assert new_login.status_code == 200

    admin_login = await client.post("/api/v1/auth/login", json={"email":"admin@example.com","password":"synthetic-password-only-for-tests"})
    admin_headers = {"X-CSRF-Token":admin_login.json()["csrf_token"]}
    disabled = await client.patch(f"/api/v1/auth/users/{user_id}", headers=admin_headers, json={"active":False})
    assert disabled.status_code == 200
    assert disabled.json()["active"] is False
    assert (await client.post("/api/v1/auth/login", json={"email":"staff-management@example.com","password":"synthetic-replacement-password"})).status_code == 401


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(client, auth_headers):
    me = (await client.get("/api/v1/auth/me")).json()
    response = await client.patch(f"/api/v1/auth/users/{me['id']}", headers=auth_headers, json={"active":False})
    assert response.status_code == 409
