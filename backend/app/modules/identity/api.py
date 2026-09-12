from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.platform.config import Settings, get_settings

Role = Literal["admin", "recepcion", "profesional", "paciente"]


class CurrentUser(BaseModel):
    id: str = Field(max_length=120)
    display_name: str = Field(min_length=1, max_length=100)
    roles: list[Role]


async def current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[str | None, Header(alias="X-Dev-User", min_length=1, max_length=100, pattern=r"^[\w .@-]+$")] = None,
    role: Annotated[Role | None, Header(alias="X-Dev-Role")] = None,
) -> CurrentUser:
    if not settings.dev_auth_enabled:
        raise HTTPException(status_code=501, detail="Production authentication is not configured")
    if not user or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Development only: send X-Dev-User and X-Dev-Role headers",
        )
    return CurrentUser(id=f"dev:{user}", display_name=user, roles=[role])


def require_roles(*roles: Role):
    async def dependency(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
        if not set(user.roles).intersection(roles):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dependency


router = APIRouter(prefix="/auth", tags=["identity"])


@router.get("/me", response_model=CurrentUser)
async def me(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
    return user
