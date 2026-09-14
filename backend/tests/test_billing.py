from datetime import datetime, timezone

import pytest


async def accepted_plan(client, auth_headers):
    patient = await client.post("/api/v1/patients", headers=auth_headers, json={"first_name":"Cobro","last_name":"Sintetico","document_type":"TEST","document_number":"BILL-001"})
    assert patient.status_code == 201, patient.text
    patient_id = patient.json()["id"]
    treatment = await client.post("/api/v1/treatments", headers=auth_headers, json={"code":"BILL-001","name":"Tratamiento sintético","category":"Pruebas","default_price":500000})
    assert treatment.status_code == 201, treatment.text
    plan = await client.post(f"/api/v1/patients/{patient_id}/treatment-plans", headers=auth_headers, json={"title":"Plan facturable"})
    plan_id = plan.json()["id"]
    await client.post(f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/items", headers=auth_headers, json={"treatment_id":treatment.json()["id"],"quantity":1})
    await client.patch(f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status", headers=auth_headers, json={"status":"proposed"})
    accepted = await client.patch(f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status", headers=auth_headers, json={"status":"accepted"})
    assert accepted.status_code == 200, accepted.text
    return patient_id, plan_id


@pytest.mark.asyncio
async def test_invoice_partial_and_full_payment_preserve_balance(client, auth_headers):
    patient_id, plan_id = await accepted_plan(client, auth_headers)
    created = await client.post(f"/api/v1/patients/{patient_id}/invoices", headers=auth_headers, json={"treatment_plan_id":plan_id,"due_date":"2026-12-31"})
    assert created.status_code == 201, created.text
    invoice = created.json()
    assert invoice["number"].startswith("DS-")
    assert invoice["amount"] == "500000"
    assert invoice["balance"] == "500000"
    assert invoice["status"] == "issued"
    billable = await client.get(f"/api/v1/patients/{patient_id}/invoices/billable-plans")
    assert billable.status_code == 200
    assert billable.json() == []

    partial = await client.post(f"/api/v1/patients/{patient_id}/invoices/{invoice['id']}/payments", headers=auth_headers, json={"amount":200000,"method":"cash","paid_at":datetime.now(timezone.utc).isoformat()})
    assert partial.status_code == 201, partial.text
    assert partial.json()["status"] == "partially_paid"
    assert partial.json()["paid_amount"] == "200000"
    assert partial.json()["balance"] == "300000"

    excessive = await client.post(f"/api/v1/patients/{patient_id}/invoices/{invoice['id']}/payments", headers=auth_headers, json={"amount":300001,"method":"transfer","paid_at":datetime.now(timezone.utc).isoformat()})
    assert excessive.status_code == 409
    completed = await client.post(f"/api/v1/patients/{patient_id}/invoices/{invoice['id']}/payments", headers=auth_headers, json={"amount":300000,"method":"transfer","paid_at":datetime.now(timezone.utc).isoformat(),"reference":"REF-SINTETICA"})
    assert completed.status_code == 201, completed.text
    assert completed.json()["status"] == "paid"
    assert completed.json()["balance"] == "0"
    cannot_cancel = await client.post(f"/api/v1/patients/{patient_id}/invoices/{invoice['id']}/cancel", headers=auth_headers)
    assert cannot_cancel.status_code == 409


@pytest.mark.asyncio
async def test_invoice_requires_accepted_plan_and_is_unique(client, auth_headers):
    patient = await client.post("/api/v1/patients", headers=auth_headers, json={"first_name":"No","last_name":"Aceptado","document_type":"TEST","document_number":"BILL-002"})
    patient_id = patient.json()["id"]
    plan = await client.post(f"/api/v1/patients/{patient_id}/treatment-plans", headers=auth_headers, json={"title":"Borrador no facturable"})
    rejected = await client.post(f"/api/v1/patients/{patient_id}/invoices", headers=auth_headers, json={"treatment_plan_id":plan.json()["id"]})
    assert rejected.status_code == 409

    accepted_patient_id, accepted_plan_id = await accepted_plan(client, auth_headers)
    first = await client.post(f"/api/v1/patients/{accepted_patient_id}/invoices", headers=auth_headers, json={"treatment_plan_id":accepted_plan_id})
    assert first.status_code == 201
    duplicate = await client.post(f"/api/v1/patients/{accepted_patient_id}/invoices", headers=auth_headers, json={"treatment_plan_id":accepted_plan_id})
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_professional_cannot_access_financial_records(client, auth_headers):
    created = await client.post("/api/v1/auth/users", headers=auth_headers, json={"email":"profesional-finanzas@example.com","display_name":"Profesional Sintético","password":"synthetic-professional-password","role":"profesional"})
    assert created.status_code == 201, created.text
    login = await client.post("/api/v1/auth/login", json={"email":"profesional-finanzas@example.com","password":"synthetic-professional-password"})
    assert login.status_code == 200
    professional_headers = {"X-CSRF-Token":login.json()["csrf_token"]}
    denied = await client.get("/api/v1/patients/00000000-0000-0000-0000-000000000001/invoices", headers=professional_headers)
    assert denied.status_code == 403
