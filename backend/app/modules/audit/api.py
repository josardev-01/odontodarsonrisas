from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditEvent
from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.platform.database import get_session


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: str
    action: str
    resource_type: str
    resource_id: UUID | None
    outcome: str
    occurred_at: datetime


router = APIRouter(prefix="/admin/audit-events", tags=["audit"])


@router.get("", response_model=list[AuditEventRead])
async def list_audit_events(
    admin: Annotated[CurrentUser, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditEvent]:
    events = list((await session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(limit))).all())
    record_event(session, actor_id=str(admin.id), action="audit.viewed", resource_type="audit_event", resource_id=None)
    await session.commit()
    return events
