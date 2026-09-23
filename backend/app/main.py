from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.audit.api import router as audit_router
from app.modules.billing import models as billing_models  # noqa: F401
from app.modules.billing.api import router as billing_router
from app.modules.identity.api import router as identity_router
from app.modules.notifications import models as notification_models  # noqa: F401
from app.modules.notifications.api import router as notifications_router
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.patients import models as patient_models  # noqa: F401
from app.modules.odontogram import models as odontogram_models  # noqa: F401
from app.modules.odontogram.api import router as odontogram_router
from app.modules.patients.api import router as patients_router
from app.modules.patients.clinical_api import router as clinical_router
from app.modules.professionals import models as professional_models  # noqa: F401
from app.modules.professionals.api import router as professionals_router
from app.modules.professionals.models import Professional
from app.modules.reporting.api import router as reporting_router
from app.modules.scheduling import models as scheduling_models  # noqa: F401
from app.modules.scheduling.api import router as scheduling_router
from app.modules.treatments import models as treatment_models  # noqa: F401
from app.modules.treatments.api import router as treatments_router
from app.modules.treatment_plans import models as treatment_plan_models  # noqa: F401
from app.modules.treatment_plans.api import router as treatment_plans_router
from app.platform.config import get_settings
from app.platform.database import Base, SessionFactory, engine
from app.platform.errors import install_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.auto_create_schema:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    if settings.seed_synthetic_professionals:
        async with SessionFactory() as session:
            exists = await session.scalar(select(Professional.id).limit(1))
            if exists is None:
                session.add_all(
                    [
                        Professional(display_name="Dra. Ada Ejemplo", specialty="Odontologia general"),
                        Professional(display_name="Dr. Bruno Ejemplo", specialty="Ortodoncia"),
                    ]
                )
                await session.commit()
    yield
    await engine.dispose()


app = FastAPI(title="Dar Sonrisas API", version="0.1.0", lifespan=lifespan)
install_error_handlers(app)
settings = get_settings()
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )


@app.get("/api/v1/health/live", tags=["health"])
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ready", tags=["health"], response_model=None)
async def ready():
    try:
        async with SessionFactory() as session:
            await session.execute(text("SELECT 1"))
            await session.execute(text("SELECT 1 FROM patients LIMIT 1"))
            await session.execute(text("SELECT 1 FROM appointments LIMIT 1"))
            await session.execute(text("SELECT 1 FROM invoices LIMIT 1"))
            await session.execute(text("SELECT 1 FROM notifications LIMIT 1"))
    except Exception:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "unavailable"})
    return {"status": "ready"}


app.include_router(identity_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(clinical_router, prefix="/api/v1")
app.include_router(odontogram_router, prefix="/api/v1")
app.include_router(professionals_router, prefix="/api/v1")
app.include_router(scheduling_router, prefix="/api/v1")
app.include_router(treatments_router, prefix="/api/v1")
app.include_router(treatment_plans_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
