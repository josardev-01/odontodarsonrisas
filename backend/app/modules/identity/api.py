import hmac
from datetime import timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field, SecretStr
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.audit.service import record_event
from app.modules.identity.models import User, UserRole, UserSession
from app.modules.identity.security import hash_password, random_token, token_digest, verify_password
from app.platform.config import Settings, get_settings
from app.platform.database import get_session
from app.platform.types import utc_now

Role = UserRole


class CurrentUser(BaseModel):
    id: UUID
    display_name: str
    email: EmailStr
    roles: list[UserRole]


class BootstrapRequest(BaseModel):
    bootstrap_token: SecretStr
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=12, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(max_length=200)


class StaffUserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=12, max_length=200)
    role: UserRole


class SessionResponse(BaseModel):
    user: CurrentUser
    csrf_token: str


def public_user(user: User) -> CurrentUser:
    return CurrentUser(id=user.id, display_name=user.display_name, email=user.email, roles=[user.role])


def expired(value) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= utc_now()


def set_cookies(response: Response, settings: Settings, session_token: str, csrf_token: str) -> None:
    common = dict(secure=settings.session_cookie_secure, samesite="strict", path="/", max_age=settings.session_ttl_hours * 3600)
    response.set_cookie("ds_session", session_token, httponly=True, **common)
    response.set_cookie("ds_csrf", csrf_token, httponly=False, **common)


async def issue_session(session: AsyncSession, user: User, settings: Settings) -> tuple[str, str]:
    session_token, csrf_token = random_token(), random_token()
    session.add(UserSession(user_id=user.id, token_digest=token_digest(session_token), csrf_digest=token_digest(csrf_token), expires_at=utc_now() + timedelta(hours=settings.session_ttl_hours)))
    return session_token, csrf_token


async def authenticated_session(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    session_cookie: Annotated[str | None, Cookie(alias="ds_session")] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias="ds_csrf")] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> tuple[User, UserSession]:
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Authentication required")
    auth_session = await session.scalar(select(UserSession).options(joinedload(UserSession.user)).where(UserSession.token_digest == token_digest(session_cookie)))
    if auth_session is None or auth_session.revoked_at is not None or expired(auth_session.expires_at):
        raise HTTPException(status_code=401, detail="Authentication required")
    user = auth_session.user
    if not user.active or user.role == UserRole.PACIENTE:
        raise HTTPException(status_code=403, detail="Account is not enabled for staff access")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        valid = bool(csrf_cookie and csrf_header and hmac.compare_digest(csrf_cookie, csrf_header) and hmac.compare_digest(auth_session.csrf_digest, token_digest(csrf_header)))
        if not valid:
            raise HTTPException(status_code=403, detail="CSRF validation failed")
    return user, auth_session


async def current_user(auth: Annotated[tuple[User, UserSession], Depends(authenticated_session)]) -> CurrentUser:
    return public_user(auth[0])


def require_roles(*roles: UserRole | str):
    expected = {UserRole(role) for role in roles}
    async def dependency(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
        if not set(user.roles).intersection(expected):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency


router = APIRouter(prefix="/auth", tags=["identity"])


@router.post("/bootstrap", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap(payload: BootstrapRequest, response: Response, session: Annotated[AsyncSession, Depends(get_session)], settings: Annotated[Settings, Depends(get_settings)]) -> SessionResponse:
    configured = settings.bootstrap_token
    supplied = payload.bootstrap_token.get_secret_value()
    if configured is None or not hmac.compare_digest(configured.get_secret_value(), supplied):
        record_event(session, actor_id="anonymous", action="auth.bootstrap_failed", resource_type="user", resource_id=None)
        await session.commit()
        raise HTTPException(status_code=403, detail="Bootstrap unavailable")
    if await session.scalar(select(func.count()).select_from(User)):
        raise HTTPException(status_code=409, detail="Bootstrap already completed")
    user = User(email=str(payload.email).strip().casefold(), display_name=payload.display_name.strip(), password_hash=hash_password(payload.password.get_secret_value()), role=UserRole.ADMIN)
    session.add(user)
    await session.flush()
    session_token, csrf_token = await issue_session(session, user, settings)
    record_event(session, actor_id=str(user.id), action="auth.bootstrap_succeeded", resource_type="user", resource_id=user.id)
    await session.commit()
    set_cookies(response, settings, session_token, csrf_token)
    return SessionResponse(user=public_user(user), csrf_token=csrf_token)


@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest, response: Response, session: Annotated[AsyncSession, Depends(get_session)], settings: Annotated[Settings, Depends(get_settings)]) -> SessionResponse:
    user = await session.scalar(select(User).where(User.email == str(payload.email).strip().casefold()))
    valid = user is not None and verify_password(user.password_hash, payload.password.get_secret_value())
    if not valid or not user.active or user.role == UserRole.PACIENTE:
        record_event(session, actor_id="anonymous", action="auth.login_failed", resource_type="user", resource_id=user.id if user else None)
        await session.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    session_token, csrf_token = await issue_session(session, user, settings)
    record_event(session, actor_id=str(user.id), action="auth.login_succeeded", resource_type="user", resource_id=user.id)
    await session.commit()
    set_cookies(response, settings, session_token, csrf_token)
    return SessionResponse(user=public_user(user), csrf_token=csrf_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, auth: Annotated[tuple[User, UserSession], Depends(authenticated_session)], session: Annotated[AsyncSession, Depends(get_session)], settings: Annotated[Settings, Depends(get_settings)]) -> None:
    user, auth_session = auth
    auth_session.revoked_at = utc_now()
    record_event(session, actor_id=str(user.id), action="auth.logout", resource_type="session", resource_id=auth_session.id)
    await session.commit()
    response.delete_cookie("ds_session", path="/", secure=settings.session_cookie_secure, samesite="strict")
    response.delete_cookie("ds_csrf", path="/", secure=settings.session_cookie_secure, samesite="strict")


@router.get("/me", response_model=CurrentUser)
async def me(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
    return user


@router.post("/users", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    payload: StaffUserCreate,
    admin: Annotated[CurrentUser, Depends(require_roles(UserRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    if payload.role == UserRole.PACIENTE:
        raise HTTPException(status_code=422, detail="Patient accounts are deferred to V2")
    user = User(
        email=str(payload.email).strip().casefold(),
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password.get_secret_value()),
        role=payload.role,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="A user with that email already exists") from exc
    record_event(
        session,
        actor_id=str(admin.id),
        action="user.created",
        resource_type="user",
        resource_id=user.id,
    )
    await session.commit()
    await session.refresh(user)
    return public_user(user)
