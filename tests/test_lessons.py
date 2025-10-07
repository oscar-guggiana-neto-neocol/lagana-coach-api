from datetime import date, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.club import Club
from app.models.coach import Coach
from app.models.player import Player
from app.models.lesson import Lesson
from app.models.user import User
from app.models.enums import (
    SkillLevel,
    UserRole,
    LessonStatus,
    LessonType,
    LessonPaymentStatus,
)


def create_coach(db: Session) -> Coach:
    user = User(email="lesson@test.com", hashed_password=get_password_hash("pass"), role=UserRole.coach, is_active=True)
    coach = Coach(full_name="Lesson Coach", email="lesson@test.com", user=user, active=True)
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def create_club(db: Session, coach: Coach) -> Club:
    club = Club(name="Lesson Club")
    coach.clubs.append(club)
    coach.default_club = club
    db.add_all([club, coach])
    db.commit()
    db.refresh(club)
    db.refresh(coach)
    return club


def create_player(db: Session, coach: Coach) -> Player:
    player = Player(full_name="Lesson Player", skill_level=SkillLevel.beginner, active=True)
    player.coaches.append(coach)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def create_lesson(db: Session, coach: Coach, player: Player, club: Club) -> Lesson:
    lesson = Lesson(
        coach_id=coach.id,
        club_id=club.id,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        duration_minutes=60,
        total_amount=Decimal("50"),
        type=LessonType.private,
        status=LessonStatus.executed,
        payment_status=LessonPaymentStatus.open,
        club_reimbursement_amount=Decimal("17"),
    )
    lesson.players.append(player)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_update_lesson_negative_reimbursement(db_session: Session, client):
    coach = create_coach(db_session)
    player = create_player(db_session, coach)
    club = create_club(db_session, coach)
    lesson = create_lesson(db_session, coach, player, club)

    token = login(client, "lesson@test.com", "pass")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "club_reimbursement_amount": -17,
        "player_ids": [player.id],
    }
    response = client.patch(
        f"/api/v1/lessons/{lesson.id}",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["club_reimbursement_amount"] == 17
