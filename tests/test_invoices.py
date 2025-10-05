from datetime import date, time, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.coach import Coach
from app.models.enums import LessonPaymentStatus, LessonStatus, LessonType, UserRole
from app.models.lesson import Lesson
from app.models.player import Player
from app.models.user import User


def create_coach_with_player(db: Session):
    user = User(email="invoice@example.com", hashed_password=get_password_hash("pass"), role=UserRole.coach, is_active=True)
    coach = Coach(full_name="Invoice Coach", email="invoice@example.com", user=user, active=True)
    player = Player(full_name="Invoice Player", active=True)
    player.coaches.append(coach)
    db.add_all([coach, player])
    db.commit()
    db.refresh(coach)
    db.refresh(player)
    return coach, player


def create_executed_lesson(db: Session, coach: Coach, player: Player, lesson_date: date, total: int = 50, reimbursement: int = 10):
    lesson = Lesson(
        coach_id=coach.id,
        date=lesson_date,
        start_time=time(9, 0),
        end_time=time(10, 0),
        duration_minutes=60,
        total_amount=total,
        type=LessonType.private,
        status=LessonStatus.executed,
        payment_status=LessonPaymentStatus.open,
        club_reimbursement_amount=reimbursement,
    )
    lesson.players.append(player)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def login(client: TestClient) -> str:
    response = client.post("/api/v1/auth/login", json={"email": "invoice@example.com", "password": "pass"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_invoice_generation_flow(client: TestClient, db_session: Session):
    coach, player = create_coach_with_player(db_session)
    lesson1 = create_executed_lesson(db_session, coach, player, date.today())
    lesson2 = create_executed_lesson(db_session, coach, player, date.today() + timedelta(days=1))

    token = login(client)

    prepare = client.post(
        "/api/v1/invoices/generate/prepare",
        headers={"Authorization": f"Bearer {token}"},
        json={"period_start": str(date.today()), "period_end": str(date.today() + timedelta(days=7))},
    )
    assert prepare.status_code == 200
    payload = prepare.json()
    assert float(payload["total_net"]) == 80.0

    confirm = client.post(
        "/api/v1/invoices/generate/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "period_start": str(date.today()),
            "period_end": str(date.today() + timedelta(days=7)),
            "lesson_ids": [lesson1.id, lesson2.id],
        },
    )
    assert confirm.status_code == 201
    invoice_id = confirm.json()["id"]

    issue = client.post(
        f"/api/v1/invoices/{invoice_id}/issue",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert issue.status_code == 200
    assert issue.json()["status"] == "issued"

    mark_paid = client.post(
        f"/api/v1/invoices/{invoice_id}/mark-paid",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert mark_paid.status_code == 200
    assert mark_paid.json()["status"] == "paid"
