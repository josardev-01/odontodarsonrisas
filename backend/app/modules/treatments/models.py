from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base
from app.platform.types import EntityMixin


class Treatment(EntityMixin, Base):
    __tablename__ = "treatments"

    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    default_price: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    currency: Mapped[str] = mapped_column(String(3), default="PYG")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
