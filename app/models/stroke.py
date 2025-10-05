from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin
from app.models.enums import StrokeCode


class Stroke(TimestampMixin, Base):
    __tablename__ = "strokes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[StrokeCode] = mapped_column(
        Enum(StrokeCode, name="stroke_code"), nullable=False, unique=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Stroke code={self.code}>"
