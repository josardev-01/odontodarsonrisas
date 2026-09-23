from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_search_update_and_deactivate_patient(client, auth_headers):
    document = f"SEARCH-{uuid4()}"
    created = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name":"Maria","last_name":"Buscada","document_type":"TEST","document_number":document,"phone":"+595991111111"},
    )
    assert created.status_code == 201
    patient_id = created.json()["id"]
    found = await client.get(f"/api/v1/patients?query={document}", headers=auth_headers)
    assert found.status_code == 200
    assert patient_id in {item["id"] for item in found.json()}

    updated = await client.put(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers,
        json={"first_name":"Maria","last_name":"Actualizada","phone":"+595992222222","active":False},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["last_name"] == "Actualizada"
    assert updated.json()["active"] is False
