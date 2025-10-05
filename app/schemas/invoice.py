from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import InvoiceStatus
from app.schemas.lesson import LessonRead


class InvoiceBase(BaseModel):
    period_start: date
    period_end: date


class InvoiceRead(InvoiceBase):
    id: int
    coach_id: int
    status: InvoiceStatus
    total_gross: Decimal
    total_club_reimbursement: Decimal
    total_net: Decimal
    issued_at: Optional[datetime] = None
    due_date: Optional[date] = None
    pdf_url: Optional[str] = None

    class Config:
        orm_mode = True


class InvoiceItemRead(BaseModel):
    id: int
    invoice_id: int
    lesson_id: Optional[int]
    description: str
    amount: Decimal

    class Config:
        orm_mode = True


class InvoiceDetail(InvoiceRead):
    items: List[InvoiceItemRead]


class InvoicePrepareRequest(BaseModel):
    period_start: date
    period_end: date


class InvoicePrepareLesson(BaseModel):
    lesson: LessonRead
    amount: Decimal
    club_reimbursement: Decimal


class InvoicePrepareResponse(BaseModel):
    lessons: List[InvoicePrepareLesson]
    total_gross: Decimal
    total_club_reimbursement: Decimal
    total_net: Decimal


class InvoiceConfirmRequest(BaseModel):
    period_start: date
    period_end: date
    lesson_ids: List[int]
    due_date: Optional[date] = None


class InvoiceIssueRequest(BaseModel):
    due_date: Optional[date] = None


class InvoiceMarkPaidRequest(BaseModel):
    paid_at: Optional[date] = Field(default=None, description="Optional payment date override")
