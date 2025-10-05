from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, resolve_coach
from app.db.session import get_db
from app.models.enums import InvoiceStatus, UserRole
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.common import Message, PaginatedResponse
from app.schemas.invoice import (
    InvoiceConfirmRequest,
    InvoiceDetail,
    InvoiceIssueRequest,
    InvoiceMarkPaidRequest,
    InvoicePrepareRequest,
    InvoicePrepareResponse,
    InvoiceRead,
)
from app.services import invoice as invoice_service

router = APIRouter(prefix="/invoices", tags=["Invoices"])


def _scoped_query(db: Session, user: User):
    query = db.query(Invoice)
    if user.role == UserRole.coach:
        coach = resolve_coach(current_user=user, db=db)
        query = query.filter(Invoice.coach_id == coach.id)
    return query


@router.get("/", response_model=PaginatedResponse[InvoiceRead])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    status_filter: Optional[InvoiceStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    query = _scoped_query(db, current_user)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    if date_from:
        query = query.filter(Invoice.period_start >= date_from)
    if date_to:
        query = query.filter(Invoice.period_end <= date_to)

    total = query.count()
    invoices = query.order_by(Invoice.period_end.desc()).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=invoices, total=total, page=page, size=size)


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if current_user.role == UserRole.coach and invoice.coach_id != resolve_coach(current_user=current_user, db=db).id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return invoice


@router.post("/generate/prepare", response_model=InvoicePrepareResponse)
def prepare_invoice(
    payload: InvoicePrepareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Preparation is coach only")

    coach = resolve_coach(current_user=current_user, db=db)
    results = invoice_service.prepare_invoice(
        db=db,
        coach_id=coach.id,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    lessons_payload = [
        {
            "lesson": lesson,
            "amount": lesson.total_amount,
            "club_reimbursement": lesson.club_reimbursement_amount or 0,
        }
        for lesson in results["lessons"]
    ]
    totals = results["totals"]
    return InvoicePrepareResponse(
        lessons=lessons_payload,
        total_gross=totals.total_gross,
        total_club_reimbursement=totals.total_club_reimbursement,
        total_net=totals.total_net,
    )


@router.post("/generate/confirm", response_model=InvoiceDetail, status_code=status.HTTP_201_CREATED)
def confirm_invoice(
    payload: InvoiceConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Confirmation is coach only")
    coach = resolve_coach(current_user=current_user, db=db)
    invoice = invoice_service.confirm_invoice(
        db=db,
        coach_id=coach.id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        lesson_ids=payload.lesson_ids,
        due_date=payload.due_date,
    )
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/issue", response_model=InvoiceDetail)
def issue_invoice(
    invoice_id: int,
    payload: InvoiceIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if current_user.role == UserRole.coach and invoice.coach_id != resolve_coach(current_user=current_user, db=db).id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if payload.due_date:
        invoice.due_date = payload.due_date

    invoice = invoice_service.issue_invoice(db, invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceDetail)
def mark_invoice_paid(
    invoice_id: int,
    payload: InvoiceMarkPaidRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if current_user.role == UserRole.coach and invoice.coach_id != resolve_coach(current_user=current_user, db=db).id:
        raise HTTPException(status_code=403, detail="Forbidden")

    invoice = invoice_service.mark_invoice_paid(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
