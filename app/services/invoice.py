from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import InvoiceStatus, LessonStatus
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.lesson import Lesson

storage_dir = Path(settings.file_storage_dir) / "invoices"
storage_dir.mkdir(parents=True, exist_ok=True)


class InvoiceTotals:
    def __init__(self, gross: Decimal, reimbursement: Decimal) -> None:
        self.total_gross = gross
        self.total_club_reimbursement = reimbursement
        self.total_net = gross - reimbursement


def _calculate_totals(lessons: Iterable[Lesson]) -> InvoiceTotals:
    gross = Decimal("0.00")
    reimbursement = Decimal("0.00")
    for lesson in lessons:
        gross += Decimal(lesson.total_amount)
        reimbursement += Decimal(lesson.club_reimbursement_amount or 0)
    return InvoiceTotals(gross=gross, reimbursement=reimbursement)


def _lesson_already_invoiced(lesson: Lesson) -> bool:
    return any(item.invoice_id for item in lesson.invoice_items)


def prepare_invoice(db: Session, coach_id: int, period_start, period_end) -> dict:
    lessons = (
        db.query(Lesson)
        .filter(
            Lesson.coach_id == coach_id,
            Lesson.date >= period_start,
            Lesson.date <= period_end,
            Lesson.status == LessonStatus.executed,
        )
        .all()
    )
    lessons = [lesson for lesson in lessons if not _lesson_already_invoiced(lesson)]
    totals = _calculate_totals(lessons)
    return {"lessons": lessons, "totals": totals}


def confirm_invoice(
    db: Session,
    coach_id: int,
    period_start,
    period_end,
    lesson_ids: List[int],
    due_date=None,
) -> Invoice:
    lessons = (
        db.query(Lesson)
        .filter(Lesson.id.in_(lesson_ids), Lesson.coach_id == coach_id)
        .all()
    )

    totals = _calculate_totals(lessons)

    invoice = Invoice(
        coach_id=coach_id,
        period_start=period_start,
        period_end=period_end,
        status=InvoiceStatus.draft,
        total_gross=totals.total_gross,
        total_club_reimbursement=totals.total_club_reimbursement,
        total_net=totals.total_net,
        due_date=due_date,
    )
    db.add(invoice)
    db.flush()

    for lesson in lessons:
        lesson_item = InvoiceItem(
            invoice=invoice,
            lesson=lesson,
            description=f"Lesson on {lesson.date} {lesson.start_time.strftime('%H:%M')}",
            amount=Decimal(lesson.total_amount),
            metadata_json={"lesson_status": lesson.status.value},
        )
        invoice.items.append(lesson_item)

        reimbursement = Decimal(lesson.club_reimbursement_amount or 0)
        if reimbursement:
            reimbursement_item = InvoiceItem(
                invoice=invoice,
                lesson=lesson,
                description="Club reimbursement",
                amount=-reimbursement,
                metadata_json={"type": "club_reimbursement"},
            )
            invoice.items.append(reimbursement_item)

        lesson.status = LessonStatus.invoiced

    db.flush()
    return invoice


def issue_invoice(db: Session, invoice: Invoice) -> Invoice:
    invoice.status = InvoiceStatus.issued
    invoice.issued_at = datetime.utcnow()
    _write_invoice_documents(invoice)
    db.add(invoice)
    return invoice


def mark_invoice_paid(invoice: Invoice) -> Invoice:
    invoice.status = InvoiceStatus.paid
    return invoice


def _write_invoice_documents(invoice: Invoice) -> None:
    pdf_path = storage_dir / f"invoice-{invoice.id}.pdf"
    csv_path = storage_dir / f"invoice-{invoice.id}.csv"

    _build_invoice_pdf(invoice, pdf_path)
    _build_invoice_csv(invoice, csv_path)

    invoice.pdf_url = str(pdf_path)


def _build_invoice_pdf(invoice: Invoice, path: Path) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=36,
        bottomMargin=36,
        leftMargin=40,
        rightMargin=40,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Right", alignment=TA_RIGHT, fontSize=10))
    styles.add(ParagraphStyle(name="Small", fontSize=9))

    coach = invoice.coach
    club = None
    for item in invoice.items:
        lesson = item.lesson
        if lesson and lesson.club:
            club = lesson.club
            break

    story: list = []

    header_left_lines = [
        f"<b>{coach.full_name}</b>",
        coach.address_line1 or "",
        coach.address_line2 or "",
    ]
    city_line = " ".join(filter(None, [coach.city, coach.postcode]))
    if city_line:
        header_left_lines.append(city_line)
    if coach.phone:
        header_left_lines.append(f"Phone: {coach.phone}")
    if coach.email:
        header_left_lines.append(coach.email)

    header_left = Paragraph("<br/>".join(filter(None, header_left_lines)), styles["BodyText"])

    issued_date = invoice.issued_at or invoice.created_at
    invoice_meta = [
        [Paragraph("<b>INVOICE</b>", styles["Heading2"]), ""],
        [Paragraph("Invoice #", styles["Small"]), Paragraph(str(invoice.id), styles["Right"])],
        [Paragraph("Date", styles["Small"]), Paragraph(issued_date.strftime("%d %b %Y"), styles["Right"])],
        [Paragraph("Period", styles["Small"]), Paragraph(f"{invoice.period_start:%d %b %Y} - {invoice.period_end:%d %b %Y}", styles["Right"])],
    ]
    if invoice.due_date:
        invoice_meta.append([Paragraph("Due Date", styles["Small"]), Paragraph(invoice.due_date.strftime("%d %b %Y"), styles["Right"])])

    invoice_meta_table = Table(invoice_meta, colWidths=[90, 110])
    invoice_meta_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    header_table = Table([[header_left, "", invoice_meta_table]], colWidths=[250, 20, 200])
    header_table.setStyle(
        TableStyle(
            [
                ("SPAN", (2, 0), (2, 0)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 18))

    bill_to_lines = []
    if club:
        bill_to_lines.append(f"<b>{club.name}</b>")
        bill_to_lines.extend(filter(None, [club.address_line1, club.address_line2]))
        city_line = " ".join(filter(None, [club.city, club.postcode]))
        if city_line:
            bill_to_lines.append(city_line)
        if club.email:
            bill_to_lines.append(club.email)
        if club.phone:
            bill_to_lines.append(club.phone)
    else:
        bill_to_lines.append(f"<b>{coach.full_name}</b>")
        bill_to_lines.extend(filter(None, [coach.address_line1, coach.address_line2]))
        city_line = " ".join(filter(None, [coach.city, coach.postcode]))
        if city_line:
            bill_to_lines.append(city_line)
        if coach.email:
            bill_to_lines.append(coach.email)
        if coach.phone:
            bill_to_lines.append(coach.phone)

    bill_to_table = Table(
        [
            [Paragraph("<b>BILL TO</b>", styles["Small"]), Paragraph("<br/>".join(filter(None, bill_to_lines)), styles["BodyText"])],
        ],
        colWidths=[70, 400],
    )
    bill_to_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(bill_to_table)
    story.append(Spacer(1, 18))

    line_items = [["DESCRIPTION", "QTY", "UNIT PRICE", "AMOUNT"]]
    for item in invoice.items:
        qty = 1
        amount = Decimal(item.amount)
        unit_price = amount
        line_items.append(
            [
                Paragraph(item.description, styles["BodyText"]),
                Paragraph(str(qty), styles["BodyText"]),
                Paragraph(f"£{unit_price:.2f}", styles["BodyText"]),
                Paragraph(f"£{amount:.2f}", styles["Right"]),
            ]
        )

    items_table = Table(line_items, colWidths=[300, 50, 70, 70])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 12))

    totals_data = [
        ["SUBTOTAL", Paragraph(f"£{Decimal(invoice.total_gross):.2f}", styles["Right"])],
        ["CLUB REIMBURSEMENT", Paragraph(f"£{Decimal(invoice.total_club_reimbursement):.2f}", styles["Right"])],
        ["TOTAL", Paragraph(f"£{Decimal(invoice.total_net):.2f}", styles["Right"])],
    ]

    totals_table = Table(totals_data, colWidths=[150, 100])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 20))

    bank_lines = [
        "<b>Bank Details</b>",
    ]
    if coach.bank_name:
        bank_lines.append(f"Bank: {coach.bank_name}")
    if coach.account_holder_name:
        bank_lines.append(f"Account Holder: {coach.account_holder_name}")
    if coach.sort_code:
        bank_lines.append(f"Sort Code: {coach.sort_code}")
    if coach.account_number:
        bank_lines.append(f"Account Number: {coach.account_number}")
    if coach.iban:
        bank_lines.append(f"IBAN: {coach.iban}")
    if coach.swift_bic:
        bank_lines.append(f"SWIFT/BIC: {coach.swift_bic}")

    if len(bank_lines) > 1:
        story.append(Paragraph("<br/>".join(bank_lines), styles["BodyText"]))
        story.append(Spacer(1, 12))

    contact_parts = [coach.full_name]
    if coach.phone:
        contact_parts.append(coach.phone)
    if coach.email:
        contact_parts.append(coach.email)

    story.append(Paragraph("If you have any questions about this invoice, please contact", styles["Small"]))
    story.append(Paragraph(" - ".join(filter(None, contact_parts)), styles["Small"]))

    doc.build(story)


def _build_invoice_csv(invoice: Invoice, path: Path) -> None:
    import csv

    with path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Description", "Amount"])
        for item in invoice.items:
            writer.writerow([item.description, f"{Decimal(item.amount):.2f}"])
        writer.writerow(["Total Gross", f"{Decimal(invoice.total_gross):.2f}"])
        writer.writerow([
            "Total Club Reimbursement",
            f"{Decimal(invoice.total_club_reimbursement):.2f}",
        ])
        writer.writerow(["Total Net", f"{Decimal(invoice.total_net):.2f}"])
