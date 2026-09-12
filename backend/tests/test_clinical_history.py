from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_professional_can_manage_append_only_clinical_history(client, auth_headers):
    patient = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "first_name": "Historia",
            "last_name": "Sintetica",
            "document_type": "TEST",
            "document_number": "CLIN-001",
            "address": "Direccion sintetica",
            "city": "Asuncion",
            "emergency_contact_name": "Contacto Sintetico",
            "emergency_contact_phone": "+595000000",
        },
    )
    assert patient.status_code == 201, patient.text
    patient_id = patient.json()["id"]

    staff = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={
            "email": "odontologo@example.com",
            "display_name": "Profesional Sintetico",
            "password": "synthetic-password-only-for-tests",
            "role": "profesional",
        },
    )
    assert staff.status_code == 201, staff.text
    await client.post("/api/v1/auth/logout", headers=auth_headers)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "odontologo@example.com", "password": "synthetic-password-only-for-tests"},
    )
    csrf = {"X-CSRF-Token": login.json()["csrf_token"]}

    profile = await client.put(
        f"/api/v1/patients/{patient_id}/clinical-profile",
        headers=csrf,
        json={
            "blood_type": "O+",
            "allergies": ["Penicilina"],
            "medications": [],
            "medical_conditions": ["Hipertension"],
            "observations": "Datos completamente sinteticos.",
        },
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["allergies"] == ["Penicilina"]

    entry = await client.post(
        f"/api/v1/patients/{patient_id}/clinical-entries",
        headers=csrf,
        json={
            "entry_type": "consultation",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "summary": "Evaluacion inicial sintetica",
            "notes": "Nota clinica sintetica sin datos reales.",
        },
    )
    assert entry.status_code == 201, entry.text
    entries = await client.get(f"/api/v1/patients/{patient_id}/clinical-entries")
    assert entries.status_code == 200
    assert [item["id"] for item in entries.json()] == [entry.json()["id"]]
    immutable = await client.patch(f"/api/v1/patients/{patient_id}/clinical-entries/{entry.json()['id']}", headers=csrf)
    assert immutable.status_code == 404


@pytest.mark.asyncio
async def test_reception_cannot_read_clinical_profile(client, auth_headers):
    created = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={
            "email": "recepcion-clinical@example.com",
            "display_name": "Recepcion Clinica Sintetica",
            "password": "synthetic-password-only-for-tests",
            "role": "recepcion",
        },
    )
    assert created.status_code == 201, created.text
    await client.post("/api/v1/auth/logout", headers=auth_headers)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "recepcion-clinical@example.com", "password": "synthetic-password-only-for-tests"},
    )
    assert login.status_code == 200
    response = await client.get("/api/v1/patients/00000000-0000-0000-0000-000000000001/clinical-profile")
    assert response.status_code == 403
