import pytest


PDF = b"%PDF-1.4\nSynthetic signed clinical history\n%%EOF"


@pytest.mark.asyncio
async def test_clinical_history_scan_versions_and_download(client, auth_headers):
    response = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Paciente", "last_name": "Sintetico", "document_type": "TEST", "document_number": "HISTORY-SCAN"},
    )
    assert response.status_code == 201, response.text
    patient_id = response.json()["id"]
    base = f"/api/v1/patients/{patient_id}/clinical-history-documents"

    first = await client.post(base, headers=auth_headers, files={"attachment": ("historial.pdf", PDF, "application/pdf")})
    assert first.status_code == 201, first.text
    assert first.json()["attachment_filename"] == "historial.pdf"
    assert first.json()["attachment_size"] == len(PDF)
    assert "attachment_data" not in first.json()

    second = await client.post(base, headers=auth_headers, files={"attachment": ("historial-actualizado.pdf", PDF + b"\nrevision", "application/pdf")})
    assert second.status_code == 201, second.text
    listed = await client.get(base)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [second.json()["id"], first.json()["id"]]

    previous = await client.get(f"{base}/{first.json()['id']}/attachment")
    assert previous.status_code == 200
    assert previous.content == PDF
    assert previous.headers["cache-control"] == "private, no-store"
    assert previous.headers["x-content-type-options"] == "nosniff"

    another = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Otro", "last_name": "Paciente", "document_type": "TEST", "document_number": "HISTORY-OTHER"},
    )
    assert another.status_code == 201
    assert (await client.get(f"/api/v1/patients/{another.json()['id']}/clinical-history-documents/{first.json()['id']}/attachment")).status_code == 404


@pytest.mark.asyncio
async def test_clinical_history_scan_rejects_invalid_file_and_reception(client, auth_headers):
    response = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Paciente", "last_name": "Sintetico", "document_type": "TEST", "document_number": "HISTORY-ROLE"},
    )
    patient_id = response.json()["id"]
    base = f"/api/v1/patients/{patient_id}/clinical-history-documents"
    invalid = await client.post(base, headers=auth_headers, files={"attachment": ("falso.pdf", b"not a PDF", "application/pdf")})
    assert invalid.status_code == 415
    created = await client.post(base, headers=auth_headers, files={"attachment": ("historial.pdf", PDF, "application/pdf")})
    assert created.status_code == 201
    staff = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={"email": "history-reception@example.com", "display_name": "Recepcion sintetica", "password": "synthetic-reception-password", "role": "recepcion"},
    )
    assert staff.status_code == 201, staff.text
    await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert (await client.get(base)).status_code == 401
    login = await client.post("/api/v1/auth/login", json={"email": "history-reception@example.com", "password": "synthetic-reception-password"})
    assert login.status_code == 200
    assert (await client.get(base)).status_code == 403
    assert (await client.get(f"{base}/{created.json()['id']}/attachment")).status_code == 403
    assert (await client.post(base, headers={"X-CSRF-Token": login.json()["csrf_token"]}, files={"attachment": ("otro.pdf", PDF, "application/pdf")})).status_code == 403
