from datetime import date as dt_date, datetime as dt_datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import InvoiceStatus

if TYPE_CHECKING:
    from app.models.coach import Coach
    from app.models.invoice_item import InvoiceItem


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[dt_date] = mapped_column(Date, nullable=False)
    period_end: Mapped[dt_date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"), default=InvoiceStatus.draft, nullable=False
    )
    total_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_club_reimbursement: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_net: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    issued_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[dt_date]] = mapped_column(Date)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(512))

    coach: Mapped["Coach"] = relationship("Coach", back_populates="invoices", lazy="joined")
    items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice id={self.id} coach={self.coach_id}>"
