from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest


async def create_appointment(client, auth_headers):
    patient = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name":"Agenda","last_name":"Prueba","document_type":"TEST","document_number":f"AGENDA-{uuid4()}"},
    )
    professional = (await client.get("/api/v1/professionals", headers=auth_headers)).json()[0]
    starts_at = datetime.now(timezone.utc) + timedelta(days=4)
    response = await client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={"patient_id":patient.json()["id"],"professional_id":professional["id"],"starts_at":starts_at.isoformat(),"ends_at":(starts_at+timedelta(minutes=45)).isoformat(),"reason":"Control"},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_reschedule_and_complete_appointment(client, auth_headers):
    appointment = await create_appointment(client, auth_headers)
    new_start = datetime.now(timezone.utc) + timedelta(days=5)
    rescheduled = await client.patch(
        f"/api/v1/appointments/{appointment['id']}/schedule",
        headers=auth_headers,
        json={"starts_at":new_start.isoformat(),"ends_at":(new_start+timedelta(minutes=30)).isoformat()},
    )
    assert rescheduled.status_code == 200, rescheduled.text
    completed = await client.patch(
        f"/api/v1/appointments/{appointment['id']}/status",
        headers=auth_headers,
        json={"status":"completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert (await client.patch(f"/api/v1/appointments/{appointment['id']}/status", headers=auth_headers, json={"status":"cancelled"})).status_code == 409


@pytest.mark.asyncio
async def test_cancelled_appointment_releases_time_slot(client, auth_headers):
    appointment = await create_appointment(client, auth_headers)
    cancelled = await client.patch(
        f"/api/v1/appointments/{appointment['id']}/status",
        headers=auth_headers,
        json={"status":"cancelled"},
    )
    assert cancelled.status_code == 200
    recreated = await client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={key:appointment[key] for key in ("patient_id","professional_id","starts_at","ends_at","reason")},
    )
    assert recreated.status_code == 201, recreated.text
