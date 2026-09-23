from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.api import CurrentUser, require_roles
from app.modules.audit.service import record_event
from app.modules.professionals.models import Professional
from app.platform.database import get_session
from app.platform.errors import NotFoundError


class ProfessionalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_name: str
    specialty: str
    active: bool
    created_at: datetime


class ProfessionalCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=160)
    specialty: str = Field(min_length=2, max_length=120)

    @field_validator("display_name", "specialty")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Must contain at least two non-space characters")
        return normalized


class ProfessionalUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=160)
    specialty: str | None = Field(default=None, min_length=2, max_length=120)
    active: bool | None = None

    @field_validator("display_name", "specialty")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Must contain at least two non-space characters")
        return normalized


router = APIRouter(prefix="/professionals", tags=["professionals"])


@router.get("", response_model=list[ProfessionalRead])
async def list_professionals(
    user: Annotated[CurrentUser, Depends(require_roles("admin", "recepcion"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    include_inactive: Annotated[bool, Query()] = False,
) -> list[Professional]:
    statement = select(Professional).order_by(Professional.display_name)
    if not include_inactive or "admin" not in user.roles:
        statement = statement.where(Professional.active.is_(True))
    return list((await session.scalars(statement)).all())


@router.post("", response_model=ProfessionalRead, status_code=status.HTTP_201_CREATED)
async def create_professional(
    payload: ProfessionalCreate,
    admin: Annotated[CurrentUser, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Professional:
    professional = Professional(
        display_name=payload.display_name.strip(),
        specialty=payload.specialty.strip(),
    )
    session.add(professional)
    await session.flush()
    record_event(session, actor_id=str(admin.id), action="professional.created", resource_type="professional", resource_id=professional.id)
    await session.commit()
    await session.refresh(professional)
    return professional


@router.patch("/{professional_id}", response_model=ProfessionalRead)
async def update_professional(
    professional_id: UUID,
    payload: ProfessionalUpdate,
    admin: Annotated[CurrentUser, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Professional:
    professional = await session.get(Professional, professional_id)
    if professional is None:
        raise NotFoundError("Professional not found")
    changes = payload.model_dump(exclude_unset=True)
    for field in ("display_name", "specialty"):
        if field in changes:
            changes[field] = changes[field].strip()
    for field, value in changes.items():
        setattr(professional, field, value)
    record_event(session, actor_id=str(admin.id), action="professional.updated", resource_type="professional", resource_id=professional.id)
    await session.commit()
    await session.refresh(professional)
    return professional
