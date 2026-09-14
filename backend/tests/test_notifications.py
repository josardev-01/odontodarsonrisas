from datetime import datetime, timezone

import pytest

from app.main import app
from app.modules.notifications.api import router as notifications_router


# Keep the module testable before its composition-root/migration integration lands.
if not any(getattr(route, "path", None) == "/api/v1/patients/{patient_id}/notifications" for route in app.routes):
    app.include_router(notifications_router, prefix="/api/v1")


async def create_patient(client, auth_headers, *, suffix: str, phone: str = "+595981123456") -> str:
    response = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Notificacion",
            "document_type": "TEST",
            "document_number": f"NOTIFY-{suffix}",
            "phone": phone,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def grant(client, auth_headers, patient_id: str, channel: str = "whatsapp"):
    return await client.post(
        f"/api/v1/patients/{patient_id}/notification-consents",
        headers=auth_headers,
        json={"channel": channel, "granted_at": datetime.now(timezone.utc).isoformat(), "evidence_location": "Archivo físico sintético NOTIFY-001"},
    )


@pytest.mark.asyncio
async def test_notification_requires_channel_opt_in_and_valid_phone(client, auth_headers):
    patient_id = await create_patient(client, auth_headers, suffix="NO-CONSENT")
    payload = {"channel": "whatsapp", "template_key": "appointment.reminder", "message": "Recordatorio de su cita."}
    denied = await client.post(f"/api/v1/patients/{patient_id}/notifications", headers=auth_headers, json=payload)
    assert denied.status_code == 409

    consent = await grant(client, auth_headers, patient_id)
    assert consent.status_code == 201, consent.text
    assert consent.json()["status"] == "granted"
    queued = await client.post(f"/api/v1/patients/{patient_id}/notifications", headers=auth_headers, json=payload)
    assert queued.status_code == 201, queued.text
    assert queued.json()["status"] == "pending"
    assert queued.json()["recipient"] == "+595981123456"

    invalid_id = await create_patient(client, auth_headers, suffix="BAD-PHONE", phone="0981 123456")
    assert (await grant(client, auth_headers, invalid_id, "sms")).status_code == 201
    invalid = await client.post(
        f"/api/v1/patients/{invalid_id}/notifications",
        headers=auth_headers,
        json={"channel": "sms", "message": "Recordatorio de su cita."},
    )
    assert invalid.status_code == 409


@pytest.mark.asyncio
async def test_revoke_consent_blocks_new_notifications(client, auth_headers):
    patient_id = await create_patient(client, auth_headers, suffix="REVOKE")
    assert (await grant(client, auth_headers, patient_id, "sms")).status_code == 201
    queued = await client.post(
        f"/api/v1/patients/{patient_id}/notifications",
        headers=auth_headers,
        json={"channel": "sms", "message": "Recordatorio de su cita."},
    )
    assert queued.status_code == 201
    revoked = await client.post(
        f"/api/v1/patients/{patient_id}/notification-consents/sms/revoke", headers=auth_headers
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    denied = await client.post(
        f"/api/v1/patients/{patient_id}/notifications",
        headers=auth_headers,
        json={"channel": "sms", "message": "Recordatorio de su cita."},
    )
    assert denied.status_code == 409
    listed = await client.get(f"/api/v1/patients/{patient_id}/notifications", headers=auth_headers)
    assert listed.json()[0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_pending_notification_can_be_cancelled_and_listed(client, auth_headers):
    patient_id = await create_patient(client, auth_headers, suffix="CANCEL")
    await grant(client, auth_headers, patient_id)
    queued = await client.post(
        f"/api/v1/patients/{patient_id}/notifications",
        headers=auth_headers,
        json={"channel": "whatsapp", "message": "Le recordamos su cita."},
    )
    notification_id = queued.json()["id"]
    cancelled = await client.post(
        f"/api/v1/patients/{patient_id}/notifications/{notification_id}/cancel", headers=auth_headers
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    assert (await client.post(f"/api/v1/patients/{patient_id}/notifications/{notification_id}/cancel", headers=auth_headers)).status_code == 409
    listed = await client.get(f"/api/v1/patients/{patient_id}/notifications", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == notification_id


@pytest.mark.asyncio
async def test_admin_records_delivery_result_and_professional_is_denied(client, auth_headers):
    patient_id = await create_patient(client, auth_headers, suffix="RESULT")
    await grant(client, auth_headers, patient_id, "sms")
    queued = await client.post(
        f"/api/v1/patients/{patient_id}/notifications",
        headers=auth_headers,
        json={"channel": "sms", "message": "Le recordamos su cita."},
    )
    result = await client.post(
        f"/api/v1/patients/{patient_id}/notifications/{queued.json()['id']}/result",
        headers=auth_headers,
        json={"status": "sent", "provider_reference": "synthetic-provider-id"},
    )
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "sent"

    created = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={"email": "notify-professional@example.com", "display_name": "Profesional", "password": "synthetic-professional-password", "role": "profesional"},
    )
    assert created.status_code == 201, created.text
    login = await client.post("/api/v1/auth/login", json={"email": "notify-professional@example.com", "password": "synthetic-professional-password"})
    professional_headers = {"X-CSRF-Token": login.json()["csrf_token"]}
    denied = await client.get(f"/api/v1/patients/{patient_id}/notifications", headers=professional_headers)
    assert denied.status_code == 403
