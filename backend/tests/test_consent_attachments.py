import json
from datetime import datetime, timezone

import pytest


PDF = b"%PDF-1.4\nSigned synthetic consent\n%%EOF"
PNG = b"\x89PNG\r\n\x1a\nSynthetic signed authorization"


async def patient_id(client, auth_headers, suffix: str) -> str:
    response = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Paciente", "last_name": "Adjunto", "document_type": "TEST", "document_number": suffix, "phone": "+595981123456"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.asyncio
async def test_clinical_consent_scan_round_trip_and_immutable_attachment(client, auth_headers):
    patient = await patient_id(client, auth_headers, "SCAN-CLINICAL")
    base = f"/api/v1/patients/{patient}/consents"
    metadata = {
        "consent_type": "consentimiento informado",
        "document_version": "v1",
        "purpose": "Tratamiento sintético",
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "signer_name": "Firmante Sintético",
    }
    created = await client.post(
        f"{base}/with-attachment",
        headers=auth_headers,
        data={"metadata": json.dumps(metadata)},
        files={"attachment": ("firma.pdf", PDF, "application/pdf")},
    )
    assert created.status_code == 201, created.text
    consent = created.json()
    assert consent["attachment_filename"] == "firma.pdf"
    assert consent["attachment_size"] == len(PDF)
    assert consent["evidence_location"] is None
    assert "attachment_data" not in consent

    listed = await client.get(base)
    assert listed.status_code == 200
    assert listed.json()[0]["attachment_filename"] == "firma.pdf"
    downloaded = await client.get(f"{base}/{consent['id']}/attachment")
    assert downloaded.status_code == 200
    assert downloaded.content == PDF
    assert downloaded.headers["cache-control"] == "private, no-store"
    assert downloaded.headers["content-disposition"] == 'attachment; filename="firma.pdf"'
    assert downloaded.headers["x-content-type-options"] == "nosniff"

    duplicate = await client.put(
        f"{base}/{consent['id']}/attachment",
        headers=auth_headers,
        files={"attachment": ("otra.pdf", PDF, "application/pdf")},
    )
    assert duplicate.status_code == 409
    other = await patient_id(client, auth_headers, "SCAN-OTHER")
    assert (await client.get(f"/api/v1/patients/{other}/consents/{consent['id']}/attachment")).status_code == 404


@pytest.mark.asyncio
async def test_signed_scan_validation_and_legacy_attachment(client, auth_headers):
    patient = await patient_id(client, auth_headers, "SCAN-VALIDATION")
    base = f"/api/v1/patients/{patient}/consents"
    metadata = {
        "consent_type": "consentimiento",
        "document_version": "v1",
        "purpose": "Prueba sintética",
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "signer_name": "Paciente Sintético",
    }
    for name, data, expected in (
        ("mal.pdf", b"<html>not a scan</html>", 415),
        ("mal.txt", PDF, 422),
        ("vacio.pdf", b"", 422),
        ("grande.pdf", PDF + b"x" * (10 * 1024 * 1024), 413),
    ):
        response = await client.post(
            f"{base}/with-attachment",
            headers=auth_headers,
            data={"metadata": json.dumps(metadata)},
            files={"attachment": (name, data, "application/pdf")},
        )
        assert response.status_code == expected, response.text
    assert (await client.get(base)).json() == []

    legacy = await client.post(base, headers=auth_headers, json={**metadata, "evidence_location": "Archivo físico"})
    assert legacy.status_code == 201
    attached = await client.put(
        f"{base}/{legacy.json()['id']}/attachment",
        headers=auth_headers,
        files={"attachment": ("archivo.pdf", PDF, "application/pdf")},
    )
    assert attached.status_code == 200, attached.text
    assert attached.json()["attachment_filename"] == "archivo.pdf"


@pytest.mark.asyncio
async def test_notification_authorization_scans_keep_prior_signed_versions(client, auth_headers):
    patient = await patient_id(client, auth_headers, "SCAN-NOTIFY")
    base = f"/api/v1/patients/{patient}/notification-consents"
    metadata = {"channel": "whatsapp", "granted_at": datetime.now(timezone.utc).isoformat()}
    first = await client.post(
        f"{base}/with-attachment",
        headers=auth_headers,
        data={"metadata": json.dumps(metadata)},
        files={"attachment": ("primera.png", PNG, "image/png")},
    )
    assert first.status_code == 201, first.text
    assert first.json()["attachment_filename"] == "primera.png"
    assert (await client.post(f"{base}/with-attachment", headers=auth_headers, data={"metadata": json.dumps(metadata)}, files={"attachment": ("otra.png", PNG, "image/png")})).status_code == 409
    assert (await client.post(f"{base}/whatsapp/revoke", headers=auth_headers)).status_code == 200
    assert (await client.post(f"/api/v1/patients/{patient}/notifications", headers=auth_headers, json={"channel": "whatsapp", "message": "Recordatorio sintético"})).status_code == 409

    second = await client.post(
        f"{base}/with-attachment",
        headers=auth_headers,
        data={"metadata": json.dumps(metadata)},
        files={"attachment": ("segunda.pdf", PDF, "application/pdf")},
    )
    assert second.status_code == 201, second.text
    listed = (await client.get(base)).json()
    assert len(listed) == 2
    assert listed[0]["id"] == second.json()["id"]
    assert listed[1]["status"] == "revoked"
    old_scan = await client.get(f"{base}/{first.json()['id']}/attachment")
    assert old_scan.status_code == 200
    assert old_scan.content == PNG
    new_scan = await client.get(f"{base}/{second.json()['id']}/attachment")
    assert new_scan.content == PDF
    queued = await client.post(f"/api/v1/patients/{patient}/notifications", headers=auth_headers, json={"channel": "whatsapp", "message": "Recordatorio sintético"})
    assert queued.status_code == 201, queued.text


@pytest.mark.asyncio
async def test_document_endpoints_require_staff_session(client, auth_headers):
    patient = await patient_id(client, auth_headers, "SCAN-AUTH")
    base = f"/api/v1/patients/{patient}/consents"
    created = await client.post(
        base,
        headers=auth_headers,
        json={
            "consent_type": "consentimiento",
            "document_version": "v1",
            "purpose": "Prueba",
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "signer_name": "Paciente Sintético",
            "evidence_location": "Archivo físico",
        },
    )
    assert created.status_code == 201
    await client.post("/api/v1/auth/logout", headers=auth_headers)
    url = f"{base}/{created.json()['id']}/attachment"
    assert (await client.get(url)).status_code == 401
    denied = await client.put(url, files={"attachment": ("firma.pdf", PDF, "application/pdf")})
    assert denied.status_code == 401


@pytest.mark.asyncio
async def test_professional_cannot_download_notification_authorization(client, auth_headers):
    patient = await patient_id(client, auth_headers, "SCAN-ROLE")
    created = await client.post(
        f"/api/v1/patients/{patient}/notification-consents/with-attachment",
        headers=auth_headers,
        data={"metadata": json.dumps({"channel": "sms", "granted_at": datetime.now(timezone.utc).isoformat()})},
        files={"attachment": ("autorizacion.pdf", PDF, "application/pdf")},
    )
    assert created.status_code == 201, created.text
    staff = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={"email": "scan-professional@example.com", "display_name": "Profesional sintético", "password": "synthetic-professional-password", "role": "profesional"},
    )
    assert staff.status_code == 201, staff.text
    await client.post("/api/v1/auth/logout", headers=auth_headers)
    login = await client.post("/api/v1/auth/login", json={"email": "scan-professional@example.com", "password": "synthetic-professional-password"})
    assert login.status_code == 200
    url = f"/api/v1/patients/{patient}/notification-consents/{created.json()['id']}/attachment"
    assert (await client.get(url)).status_code == 403
    assert (await client.put(url, headers={"X-CSRF-Token": login.json()["csrf_token"]}, files={"attachment": ("otra.pdf", PDF, "application/pdf")})).status_code == 403
