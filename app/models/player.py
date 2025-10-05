from datetime import date as dt_date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.associations import lesson_players_table, player_coach_table
from app.models.enums import SkillLevel

if TYPE_CHECKING:
    from app.models.coach import Coach
    from app.models.lesson import Lesson


class Player(TimestampMixin, Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    birth_date: Mapped[Optional[dt_date]] = mapped_column(Date)
    skill_level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel, name="skill_level"), default=SkillLevel.beginner, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    coaches: Mapped[List["Coach"]] = relationship(
        "Coach",
        secondary=player_coach_table,
        back_populates="players",
        lazy="selectin",
    )
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        secondary=lesson_players_table,
        back_populates="players",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Player id={self.id} full_name={self.full_name}>"
