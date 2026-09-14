from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.billing.models import InvoiceStatus, PaymentMethod


class InvoiceCreate(BaseModel):
    treatment_plan_id: UUID
    due_date: date | None = None


class BillablePlanRead(BaseModel):
    id: UUID
    title: str
    total: Decimal


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=0, max_digits=14)
    method: PaymentMethod
    paid_at: datetime
    reference: str | None = Field(default=None, max_length=120)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    amount: Decimal
    method: PaymentMethod
    paid_at: datetime
    reference: str | None
    created_at: datetime


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    treatment_plan_id: UUID
    number: str
    description: str
    amount: Decimal
    currency: str
    due_date: date | None
    status: InvoiceStatus
    cancelled_at: datetime | None
    created_at: datetime
    payments: list[PaymentRead]

    @computed_field
    @property
    def paid_amount(self) -> Decimal:
        return sum((payment.amount for payment in self.payments), Decimal(0))

    @computed_field
    @property
    def balance(self) -> Decimal:
        return self.amount - self.paid_amount
