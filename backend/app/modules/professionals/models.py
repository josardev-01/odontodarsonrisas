from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base
from app.platform.types import EntityMixin


class Professional(EntityMixin, Base):
    __tablename__ = "professionals"

    display_name: Mapped[str] = mapped_column(String(160))
    specialty: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

