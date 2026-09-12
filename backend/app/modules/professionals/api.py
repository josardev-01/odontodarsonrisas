from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.api import CurrentUser, require_roles
from app.modules.professionals.models import Professional
from app.platform.database import get_session


class ProfessionalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_name: str
    specialty: str
    active: bool
    created_at: datetime


router = APIRouter(prefix="/professionals", tags=["professionals"])


@router.get("", response_model=list[ProfessionalRead])
async def list_professionals(
    user: Annotated[CurrentUser, Depends(require_roles("admin", "recepcion"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[Professional]:
    return list((await session.scalars(select(Professional).where(Professional.active.is_(True)))).all())

