from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest


async def create_partially_paid_invoice(client, auth_headers, suffix: str, paid_at: datetime) -> None:
    patient = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "first_name": "Reporte",
            "last_name": "Sintetico",
            "document_type": "TEST",
            "document_number": f"REPORT-{suffix}",
        },
    )
    assert patient.status_code == 201, patient.text
    patient_id = patient.json()["id"]
    treatment = await client.post(
        "/api/v1/treatments",
        headers=auth_headers,
        json={
            "code": f"REPORT-{suffix}",
            "name": "Tratamiento para reporte",
            "category": "Pruebas",
            "default_price": 500000,
        },
    )
    assert treatment.status_code == 201, treatment.text
    plan = await client.post(
        f"/api/v1/patients/{patient_id}/treatment-plans",
        headers=auth_headers,
        json={"title": "Plan para reporte"},
    )
    plan_id = plan.json()["id"]
    assert (
        await client.post(
            f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/items",
            headers=auth_headers,
            json={"treatment_id": treatment.json()["id"], "quantity": 1},
        )
    ).status_code == 201
    assert (
        await client.patch(
            f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status",
            headers=auth_headers,
            json={"status": "proposed"},
        )
    ).status_code == 200
    assert (
        await client.patch(
            f"/api/v1/patients/{patient_id}/treatment-plans/{plan_id}/status",
            headers=auth_headers,
            json={"status": "accepted"},
        )
    ).status_code == 200
    invoice = await client.post(
        f"/api/v1/patients/{patient_id}/invoices",
        headers=auth_headers,
        json={"treatment_plan_id": plan_id},
    )
    assert invoice.status_code == 201, invoice.text
    payment = await client.post(
        f"/api/v1/patients/{patient_id}/invoices/{invoice.json()['id']}/payments",
        headers=auth_headers,
        json={"amount": 200000, "method": "cash", "paid_at": paid_at.isoformat()},
    )
    assert payment.status_code == 201, payment.text


@pytest.mark.asyncio
async def test_admin_summary_aggregates_operations_and_finances(client, auth_headers):
    now = datetime.now(timezone.utc)
    local_today = now.astimezone(ZoneInfo("America/Asuncion")).date()
    await create_partially_paid_invoice(client, auth_headers, now.strftime("%Y%m%d%H%M%S%f"), now)
    patient = (await client.get("/api/v1/patients", headers=auth_headers)).json()[0]
    professional = (await client.get("/api/v1/professionals", headers=auth_headers)).json()[0]
    starts_at = now + timedelta(days=2)
    appointment = await client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "patient_id": patient["id"],
            "professional_id": professional["id"],
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(minutes=30)).isoformat(),
        },
    )
    assert appointment.status_code == 201, appointment.text

    response = await client.get(
        "/api/v1/admin/reports/summary",
        params={"from": local_today.isoformat(), "to": (local_today + timedelta(days=7)).isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["active_patients"] >= 1
    assert summary["appointments_in_range"] == 1
    assert summary["upcoming_appointments"] >= 1
    assert summary["collected_amount"] == "200000"
    assert summary["outstanding_balance"] == "300000"
    assert summary["invoices_by_status"]["partially_paid"] == 1
    assert summary["currency"] == "PYG"
    assert "patients" not in summary


@pytest.mark.asyncio
async def test_summary_rejects_non_admin_and_invalid_ranges(client, auth_headers):
    too_long = await client.get(
        "/api/v1/admin/reports/summary?from=2026-01-01&to=2027-01-02",
        headers=auth_headers,
    )
    assert too_long.status_code == 422
    naive = await client.get(
        "/api/v1/admin/reports/summary?from=2026-09-01T08:00:00&to=2026-09-02T08:00:00",
        headers=auth_headers,
    )
    assert naive.status_code == 422

    created = await client.post(
        "/api/v1/auth/users",
        headers=auth_headers,
        json={
            "email": "recepcion-reportes@example.com",
            "display_name": "Recepcion sin reportes",
            "password": "synthetic-reception-password",
            "role": "recepcion",
        },
    )
    assert created.status_code == 201, created.text
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "recepcion-reportes@example.com", "password": "synthetic-reception-password"},
    )
    assert login.status_code == 200
    denied = await client.get("/api/v1/admin/reports/summary?from=2026-09-01&to=2026-09-30")
    assert denied.status_code == 403
