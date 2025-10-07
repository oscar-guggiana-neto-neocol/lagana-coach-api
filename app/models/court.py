from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.associations import lesson_courts_table

if TYPE_CHECKING:
    from app.models.club import Club
    from app.models.lesson import Lesson


class Court(TimestampMixin, Base):
    __tablename__ = "courts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    club: Mapped["Club"] = relationship("Club", back_populates="courts", lazy="joined")
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        secondary=lesson_courts_table,
        back_populates="courts",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Court id={self.id} club_id={self.club_id} name={self.name}>"
