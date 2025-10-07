from datetime import date as dt_date, time as dt_time
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Time,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.associations import lesson_players_table, lesson_strokes_table, lesson_courts_table
from app.models.enums import LessonPaymentStatus, LessonStatus, LessonType

if TYPE_CHECKING:
    from app.models.coach import Coach
    from app.models.club import Club
    from app.models.player import Player
    from app.models.stroke import Stroke
    from app.models.invoice_item import InvoiceItem
    from app.models.court import Court


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coach_id: Mapped[int] = mapped_column(ForeignKey("coaches.id", ondelete="CASCADE"), index=True)
    club_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clubs.id", ondelete="SET NULL"))
    date: Mapped[dt_date] = mapped_column(Date, nullable=False)
    start_time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    end_time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    type: Mapped[LessonType] = mapped_column(Enum(LessonType, name="lesson_type"), nullable=False)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, name="lesson_status"), default=LessonStatus.draft, nullable=False
    )
    payment_status: Mapped[LessonPaymentStatus] = mapped_column(
        Enum(LessonPaymentStatus, name="lesson_payment_status"),
        default=LessonPaymentStatus.open,
        nullable=False,
    )
    club_reimbursement_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    coach: Mapped["Coach"] = relationship("Coach", back_populates="lessons", lazy="joined")
    club: Mapped[Optional["Club"]] = relationship("Club", back_populates="lessons", lazy="joined")
    players: Mapped[List["Player"]] = relationship(
        "Player",
        secondary=lesson_players_table,
        back_populates="lessons",
        lazy="selectin",
    )
    strokes: Mapped[List["Stroke"]] = relationship(
        "Stroke",
        secondary=lesson_strokes_table,
        lazy="selectin",
    )
    courts: Mapped[List["Court"]] = relationship(
        "Court",
        secondary=lesson_courts_table,
        back_populates="lessons",
        lazy="selectin",
    )
    invoice_items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_lessons_duration_positive"),
        CheckConstraint(
            "(club_reimbursement_amount IS NULL) OR (club_reimbursement_amount >= 0)",
            name="ck_lessons_reimbursement_positive",
        ),
        Index("ix_lessons_coach_date", "coach_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<Lesson id={self.id} coach={self.coach_id} date={self.date}>"
