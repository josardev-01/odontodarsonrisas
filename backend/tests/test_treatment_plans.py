import pytest


@pytest.mark.asyncio
async def test_treatment_plan_snapshots_price_and_enforces_workflow(client, auth_headers):
    patient_response = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name":"Plan","last_name":"Sintetico","document_type":"TEST","document_number":"PLAN-001"},
    )
    assert patient_response.status_code == 201, patient_response.text
    patient_id = patient_response.json()["id"]
    treatment_response = await client.post(
        "/api/v1/treatments",
        headers=auth_headers,
        json={"code":"PLAN-REST-001","name":"Restauración de prueba","category":"Restauraciones","default_price":150000},
    )
    assert treatment_response.status_code == 201, treatment_response.text
    treatment_id = treatment_response.json()["id"]

    plan_response = await client.post(
        f"/api/v1/patients/{patient_id}/treatment-plans",
        headers=auth_headers,
        json={"title":"Plan inicial","clinical_notes":"Datos completamente sintéticos","valid_until":"2026-12-31"},
    )
    assert plan_response.status_code == 201, plan_response.text
    plan_id = plan_response.json()["id"]
    assert plan_response.json()["status"] == "draft"
    assert plan_response.json()["total"] == "0"

    empty_proposal = await client.patch(
        f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status":"proposed"},
    )
    assert empty_proposal.status_code == 409

    item_response = await client.post(
        f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/items",
        headers=auth_headers,
        json={"treatment_id":treatment_id,"tooth_code":"11","quantity":2},
    )
    assert item_response.status_code == 201, item_response.text
    item = item_response.json()["items"][0]
    assert item["description"] == "Restauración de prueba"
    assert item["unit_price"] == "150000"
    assert item["subtotal"] == "300000"
    assert item_response.json()["total"] == "300000"

    proposed = await client.patch(
        f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status":"proposed"},
    )
    assert proposed.status_code == 200, proposed.text
    accepted = await client.patch(
        f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status":"accepted"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted_at"] is not None

    late_item = await client.post(
        f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/items",
        headers=auth_headers,
        json={"treatment_id":treatment_id,"quantity":1},
    )
    assert late_item.status_code == 409
    invalid_transition = await client.patch(
        f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status",
        headers=auth_headers,
        json={"status":"draft"},
    )
    assert invalid_transition.status_code == 409

    listed = await client.get(f"/api/v1/patients/{patient_id}/treatment-plans")
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "accepted"
    assert listed.json()[0]["total"] == "300000"


@pytest.mark.asyncio
async def test_treatment_plan_rejects_invalid_tooth_code(client, auth_headers):
    response = await client.post(
        "/api/v1/patients/00000000-0000-0000-0000-000000000001/treatment-plans/00000000-0000-0000-0000-000000000002/items",
        headers=auth_headers,
        json={"treatment_id":"00000000-0000-0000-0000-000000000003","tooth_code":"99","quantity":1},
    )
    assert response.status_code == 422
