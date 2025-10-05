from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.associations import player_coach_table

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.player import Player
    from app.models.lesson import Lesson
    from app.models.invoice import Invoice


class Coach(TimestampMixin, Base):
    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    postcode: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    bank_name: Mapped[Optional[str]] = mapped_column(String(150))
    account_holder_name: Mapped[Optional[str]] = mapped_column(String(150))
    sort_code: Mapped[Optional[str]] = mapped_column(String(20))
    account_number: Mapped[Optional[str]] = mapped_column(String(20))
    iban: Mapped[Optional[str]] = mapped_column(String(34))
    swift_bic: Mapped[Optional[str]] = mapped_column(String(11))
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="coach", lazy="joined")
    players: Mapped[List["Player"]] = relationship(
        "Player",
        secondary=player_coach_table,
        back_populates="coaches",
        lazy="selectin",
    )
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="coach",
        lazy="selectin",
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="coach",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Coach id={self.id} full_name={self.full_name}>"
