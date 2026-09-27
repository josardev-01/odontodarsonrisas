from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_odontogram_work_populates_budget_and_evolution_closes_each_procedure(client, auth_headers):
    patient = await client.post("/api/v1/patients", headers=auth_headers, json={
        "first_name": "Paciente", "last_name": "Sintetico", "document_type": "TEST", "document_number": "FLOW-001",
    })
    assert patient.status_code == 201
    patient_id = patient.json()["id"]
    treatment = await client.post("/api/v1/treatments", headers=auth_headers, json={
        "code": "FLOW-REST", "name": "Restauracion sintetica", "category": "Pruebas", "default_price": 150000,
    })
    assert treatment.status_code == 201
    treatment_id = treatment.json()["id"]
    for tooth in ("16", "26"):
        recorded = await client.post(f"/api/v1/patients/{patient_id}/odontogram/events", headers=auth_headers, json={
            "tooth_code": tooth, "surface": "mesial", "condition": "caries",
            "observed_at": datetime.now(timezone.utc).isoformat(), "treatment_id": treatment_id,
        })
        assert recorded.status_code == 201, recorded.text
    work_base = f"/api/v1/patients/{patient_id}/odontogram/work-items"
    work = (await client.get(work_base)).json()
    assert len(work) == 2
    assert all(item["current_plan_id"] is None and item["completed_at"] is None for item in work)
    duplicate_work = await client.post(f"/api/v1/patients/{patient_id}/odontogram/events", headers=auth_headers, json={
        "tooth_code": "16", "surface": "mesial", "condition": "caries",
        "observed_at": datetime.now(timezone.utc).isoformat(), "treatment_id": treatment_id,
    })
    assert duplicate_work.status_code == 409

    plans_base = f"/api/v1/patients/{patient_id}/treatment-plans"
    created = await client.post(plans_base, headers=auth_headers, json={"title": "Presupuesto sintetico", "from_odontogram": True})
    assert created.status_code == 201, created.text
    plan = created.json()
    assert len(plan["items"]) == 2
    assert {item["work_item_id"] for item in plan["items"]} == {item["id"] for item in work}
    assert plan["total"] == "300000"
    changed_price = await client.patch(
        f"{plans_base}/{plan['id']}/items/{plan['items'][0]['id']}/price",
        headers=auth_headers, json={"unit_price": 160000},
    )
    assert changed_price.status_code == 200, changed_price.text
    assert changed_price.json()["total"] == "310000"
    duplicate = await client.post(plans_base, headers=auth_headers, json={"title": "Duplicado", "from_odontogram": True})
    assert duplicate.status_code == 409
    for next_status in ("proposed", "accepted"):
        changed = await client.patch(f"{plans_base}/{plan['id']}/status", headers=auth_headers, json={"status": next_status})
        assert changed.status_code == 200, changed.text
    assert (await client.patch(f"{plans_base}/{plan['id']}/status", headers=auth_headers, json={"status": "in_progress"})).status_code == 200
    assert (await client.patch(f"{plans_base}/{plan['id']}/status", headers=auth_headers, json={"status": "completed"})).status_code == 409

    evolution_base = f"/api/v1/patients/{patient_id}/evolution"
    first_work = work[0]["id"]
    observed = await client.post(f"{evolution_base}/work-items/{first_work}/entries", headers=auth_headers, json={"notes": "Falta terminar"})
    assert observed.status_code == 201, observed.text
    assert observed.json()["control_completed"] is False
    assert observed.json()["notes"] == "Falta terminar"
    assert next(item for item in (await client.get(work_base)).json() if item["id"] == first_work)["completed_at"] is None
    invalid = await client.post(f"{evolution_base}/work-items/{first_work}/entries", headers=auth_headers, json={})
    assert invalid.status_code == 422

    for item in work:
        entry = await client.post(f"{evolution_base}/work-items/{item['id']}/entries", headers=auth_headers, json={"control_completed": True})
        assert entry.status_code == 201, entry.text
        assert entry.json()["control_completed"] is True
        completed = next(value for value in (await client.get(work_base)).json() if value["id"] == item["id"])
        assert completed["completed_at"] is not None
        assert completed["result_event_id"] is None
        assert (await client.post(f"{evolution_base}/work-items/{item['id']}/entries", headers=auth_headers, json={"notes": "Tarde"})).status_code == 409
    assert (await client.get(plans_base)).json()[0]["status"] == "completed"
    assert len((await client.get(f"{evolution_base}/entries")).json()) == 3
    assert len((await client.get(f"/api/v1/patients/{patient_id}/odontogram/history")).json()) == 2


@pytest.mark.asyncio
async def test_rejected_budget_releases_odontogram_work(client, auth_headers):
    patient = await client.post("/api/v1/patients", headers=auth_headers, json={
        "first_name": "Paciente", "last_name": "Sintetico", "document_type": "TEST", "document_number": "FLOW-REJECT",
    })
    patient_id = patient.json()["id"]
    treatment = await client.post("/api/v1/treatments", headers=auth_headers, json={
        "code": "FLOW-EX", "name": "Extraccion sintetica", "category": "Pruebas", "default_price": 200000,
    })
    await client.post(f"/api/v1/patients/{patient_id}/odontogram/events", headers=auth_headers, json={
        "tooth_code": "18", "surface": "whole", "condition": "extraction_indicated",
        "observed_at": datetime.now(timezone.utc).isoformat(), "treatment_id": treatment.json()["id"],
    })
    base = f"/api/v1/patients/{patient_id}/treatment-plans"
    original = await client.post(base, headers=auth_headers, json={"title": "Primero", "from_odontogram": True})
    assert original.status_code == 201, original.text
    await client.patch(f"{base}/{original.json()['id']}/status", headers=auth_headers, json={"status": "proposed"})
    rejected = await client.patch(f"{base}/{original.json()['id']}/status", headers=auth_headers, json={"status": "rejected"})
    assert rejected.status_code == 200, rejected.text
    again = await client.post(base, headers=auth_headers, json={"title": "Segundo", "from_odontogram": True})
    assert again.status_code == 201, again.text
    assert again.json()["items"][0]["work_item_id"] == original.json()["items"][0]["work_item_id"]


@pytest.mark.asyncio
async def test_reception_cannot_access_clinical_work_or_evolution(client, auth_headers):
    patient = await client.post("/api/v1/patients", headers=auth_headers, json={
        "first_name": "Paciente", "last_name": "Sintetico", "document_type": "TEST", "document_number": "FLOW-ROLE",
    })
    patient_id = patient.json()["id"]
    staff = await client.post("/api/v1/auth/users", headers=auth_headers, json={
        "email": "evolution-reception@example.com", "display_name": "Recepcion sintetica",
        "password": "synthetic-reception-password", "role": "recepcion",
    })
    assert staff.status_code == 201, staff.text
    await client.post("/api/v1/auth/logout", headers=auth_headers)
    login = await client.post("/api/v1/auth/login", json={
        "email": "evolution-reception@example.com", "password": "synthetic-reception-password",
    })
    assert login.status_code == 200
    assert (await client.get(f"/api/v1/patients/{patient_id}/odontogram/work-items")).status_code == 403
    assert (await client.get(f"/api/v1/patients/{patient_id}/evolution/entries")).status_code == 403
