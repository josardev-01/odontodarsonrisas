from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.treatments.models import Treatment
from app.platform.database import get_session
from app.platform.errors import ConflictError


class TreatmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9._-]+$")
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=100)
    default_price: Decimal = Field(ge=0, decimal_places=0, max_digits=14)


class TreatmentRead(TreatmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    currency: str
    active: bool
    created_at: datetime


router = APIRouter(prefix="/treatments", tags=["treatments"])
Db = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[TreatmentRead])
async def list_treatments(
    user: Annotated[CurrentUser, Depends(require_roles("admin", "profesional", "recepcion"))],
    session: Db,
) -> list[Treatment]:
    return list((await session.scalars(select(Treatment).where(Treatment.active.is_(True)).order_by(Treatment.category, Treatment.name))).all())


@router.post("", response_model=TreatmentRead, status_code=status.HTTP_201_CREATED)
async def create_treatment(
    payload: TreatmentCreate,
    user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    session: Db,
) -> Treatment:
    treatment = Treatment(**payload.model_dump(), currency="PYG")
    session.add(treatment)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("A treatment with that code already exists") from exc
    record_event(session, actor_id=str(user.id), action="treatment.created", resource_type="treatment", resource_id=treatment.id)
    await session.commit()
    await session.refresh(treatment)
    return treatment
