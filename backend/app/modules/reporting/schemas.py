from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class InvoiceStatusCounts(BaseModel):
    issued: int = 0
    partially_paid: int = 0
    paid: int = 0
    cancelled: int = 0


class AdministrativeSummary(BaseModel):
    from_date: date
    to_date: date
    active_patients: int
    appointments_in_range: int
    upcoming_appointments: int
    collected_amount: Decimal
    outstanding_balance: Decimal
    invoices_by_status: InvoiceStatusCounts
    currency: str = "PYG"
