import pytest


@pytest.mark.asyncio
async def test_admin_manages_professionals_and_inactive_are_hidden(client, auth_headers):
    created = await client.post(
        "/api/v1/professionals",
        headers=auth_headers,
        json={"display_name": "Dra. Sofia Prueba", "specialty": "Odontologia general"},
    )
    assert created.status_code == 201, created.text
    professional_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/professionals/{professional_id}",
        headers=auth_headers,
        json={"specialty": "Endodoncia", "active": False},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["specialty"] == "Endodoncia"
    assert updated.json()["active"] is False

    active = await client.get("/api/v1/professionals", headers=auth_headers)
    assert professional_id not in {item["id"] for item in active.json()}
    all_items = await client.get("/api/v1/professionals?include_inactive=true", headers=auth_headers)
    assert professional_id in {item["id"] for item in all_items.json()}


@pytest.mark.asyncio
async def test_reception_cannot_create_or_reveal_inactive_professionals(client, auth_headers):
    user = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={
            "email": "recepcion-profesionales@example.com",
            "display_name": "Recepcion Prueba",
            "password": "synthetic-reception-password",
            "role": "recepcion",
        },
    )
    assert user.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "recepcion-profesionales@example.com", "password": "synthetic-reception-password"},
    )
    reception_headers = {"X-CSRF-Token": login.json()["csrf_token"]}
    denied = await client.post(
        "/api/v1/professionals",
        headers=reception_headers,
        json={"display_name": "No permitido", "specialty": "General"},
    )
    assert denied.status_code == 403
    listed = await client.get("/api/v1/professionals?include_inactive=true", headers=reception_headers)
    assert listed.status_code == 200
    assert all(item["active"] for item in listed.json())
