from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_health_and_authentication(client):
    assert (await client.get("/api/v1/health/live")).status_code == 200
    assert (await client.get("/api/v1/patients")).status_code == 401
    forbidden = await client.get(
        "/api/v1/patients",
        headers={"X-Dev-User": "profesional-ejemplo", "X-Dev-Role": "profesional"},
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_create_patient_and_reject_appointment_collision(client, auth_headers):
    patient_response = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Sintetico",
            "document_type": "TEST",
            "document_number": "SYN-001",
            "birth_date": "1990-01-01",
            "phone": "+000000000",
            "email": "paciente.sintetico@example.com",
        },
    )
    assert patient_response.status_code == 201, patient_response.text
    professional_response = await client.get("/api/v1/professionals", headers=auth_headers)
    professional_id = professional_response.json()[0]["id"]
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        "patient_id": patient_response.json()["id"],
        "professional_id": professional_id,
        "starts_at": starts_at.isoformat(),
        "ends_at": (starts_at + timedelta(minutes=30)).isoformat(),
        "reason": "Consulta sintetica",
    }
    assert (await client.post("/api/v1/appointments", headers=auth_headers, json=payload)).status_code == 201
    conflict = await client.post("/api/v1/appointments", headers=auth_headers, json=payload)
    assert conflict.status_code == 409
    assert conflict.headers["content-type"].startswith("application/problem+json")


@pytest.mark.asyncio
async def test_rejects_naive_appointment_timestamps(client, auth_headers):
    response = await client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "patient_id": "00000000-0000-0000-0000-000000000001",
            "professional_id": "00000000-0000-0000-0000-000000000002",
            "starts_at": "2026-09-15T09:00:00",
            "ends_at": "2026-09-15T09:30:00",
        },
    )
    assert response.status_code == 422
