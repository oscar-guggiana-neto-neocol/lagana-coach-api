import datetime as dt
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import LessonPaymentStatus, LessonStatus, LessonType, StrokeCode
from app.schemas.court import CourtRead
from app.schemas.player import PlayerRead
from app.schemas.stroke import StrokeRead


class LessonBase(BaseModel):
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    total_amount: Decimal = Field(..., ge=0)
    type: LessonType
    status: LessonStatus = LessonStatus.draft
    payment_status: LessonPaymentStatus = LessonPaymentStatus.open
    club_id: Optional[int] = None
    club_reimbursement_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class LessonCreate(LessonBase):
    coach_id: int
    player_ids: List[int] = Field(default_factory=list)
    stroke_codes: List[StrokeCode] = Field(default_factory=list)
    court_ids: List[int] = Field(default_factory=list)


class LessonUpdate(BaseModel):
    date: Optional[dt.date] = None
    start_time: Optional[dt.time] = None
    end_time: Optional[dt.time] = None
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    type: Optional[LessonType] = None
    status: Optional[LessonStatus] = None
    payment_status: Optional[LessonPaymentStatus] = None
    club_id: Optional[int] = None
    club_reimbursement_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    player_ids: Optional[List[int]] = None
    stroke_codes: Optional[List[StrokeCode]] = None
    court_ids: Optional[List[int]] = None


class LessonRead(LessonBase):
    id: int
    duration_minutes: int
    coach_id: int
    players: List[PlayerRead]
    strokes: List[StrokeRead]
    courts: List[CourtRead]

    class Config:
        orm_mode = True


class LessonFilters(BaseModel):
    date_from: Optional[dt.date] = None
    date_to: Optional[dt.date] = None
    status: Optional[LessonStatus] = None
    payment_status: Optional[LessonPaymentStatus] = None
    club_id: Optional[int] = None
    player_id: Optional[int] = None
