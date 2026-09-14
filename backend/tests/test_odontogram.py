from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_odontogram_keeps_history_and_returns_latest_surface_state(client, auth_headers):
    patient = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "first_name": "Odontograma",
            "last_name": "Sintetico",
            "document_type": "TEST",
            "document_number": "OD-001",
        },
    )
    patient_id = patient.json()["id"]
    treatment = await client.post(
        "/api/v1/treatments",
        headers=auth_headers,
        json={"code": "REST-001", "name": "Restauracion sintetica", "category": "Restauraciones", "default_price": 150000},
    )
    assert treatment.status_code == 201, treatment.text
    treatment_id = treatment.json()["id"]
    observed = datetime.now(timezone.utc)
    first = await client.post(
        f"/api/v1/patients/{patient_id}/odontogram/events",
        headers=auth_headers,
        json={"tooth_code": "11", "surface": "buccal", "condition": "caries", "observed_at": observed.isoformat(), "note": "Hallazgo sintetico"},
    )
    assert first.status_code == 201, first.text
    second = await client.post(
        f"/api/v1/patients/{patient_id}/odontogram/events",
        headers=auth_headers,
        json={"tooth_code": "11", "surface": "buccal", "condition": "restoration", "observed_at": (observed + timedelta(minutes=5)).isoformat(), "treatment_id": treatment_id},
    )
    assert second.status_code == 201, second.text

    history = await client.get(f"/api/v1/patients/{patient_id}/odontogram/history")
    current = await client.get(f"/api/v1/patients/{patient_id}/odontogram/current")
    assert len(history.json()) == 2
    assert len(current.json()) == 1
    assert current.json()[0]["condition"] == "restoration"
    assert current.json()[0]["treatment_id"] == treatment_id


@pytest.mark.asyncio
async def test_odontogram_rejects_invalid_fdi_code(client, auth_headers):
    response = await client.post(
        "/api/v1/patients/00000000-0000-0000-0000-000000000001/odontogram/events",
        headers=auth_headers,
        json={"tooth_code": "99", "surface": "whole", "condition": "healthy", "observed_at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == 422
