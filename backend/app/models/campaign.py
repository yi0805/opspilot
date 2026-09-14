"""Marketing campaign domain model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Campaign(Base):
    """Synthetic marketing campaign performance for one product."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    channel: Mapped[str] = mapped_column(String(50))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    spend: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    attributed_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(32))

    product: Mapped["Product"] = relationship(back_populates="campaigns")
