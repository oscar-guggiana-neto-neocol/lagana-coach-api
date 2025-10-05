from datetime import date, time

from typing import List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.coach import Coach
from app.models.enums import LessonPaymentStatus, LessonStatus, LessonType, SkillLevel, UserRole
from app.models.lesson import Lesson
from app.models.player import Player
from app.models.user import User


def create_coach(db: Session, email: str, password: str, name: str) -> Coach:
    user = User(email=email, hashed_password=get_password_hash(password), role=UserRole.coach, is_active=True)
    coach = Coach(full_name=name, email=email, user=user, active=True)
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def create_player(db: Session, name: str, coach: Coach) -> Player:
    player = Player(full_name=name, skill_level=SkillLevel.beginner, active=True)
    player.coaches.append(coach)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def create_lesson(db: Session, coach: Coach, players: List[Player], status: LessonStatus = LessonStatus.executed) -> Lesson:
    lesson = Lesson(
        coach_id=coach.id,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(11, 0),
        duration_minutes=60,
        total_amount=50,
        type=LessonType.private,
        status=status,
        payment_status=LessonPaymentStatus.open,
        club_reimbursement_amount=10,
    )
    lesson.players = players
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_coach_scope_on_players_and_lessons(client: TestClient, db_session: Session):
    coach_a = create_coach(db_session, "coach_a@example.com", "passA", "Coach A")
    coach_b = create_coach(db_session, "coach_b@example.com", "passB", "Coach B")

    player_a1 = create_player(db_session, "Player Alpha", coach_a)
    player_b1 = create_player(db_session, "Player Beta", coach_b)

    create_lesson(db_session, coach_a, [player_a1])
    create_lesson(db_session, coach_b, [player_b1])

    token_a = login(client, "coach_a@example.com", "passA")

    players_response = client.get("/api/v1/players", headers={"Authorization": f"Bearer {token_a}"})
    assert players_response.status_code == 200
    players = players_response.json()["items"]
    assert len(players) == 1
    assert players[0]["full_name"] == "Player Alpha"

    lessons_response = client.get("/api/v1/lessons", headers={"Authorization": f"Bearer {token_a}"})
    assert lessons_response.status_code == 200
    lessons = lessons_response.json()["items"]
    assert len(lessons) == 1
    assert lessons[0]["coach_id"] == coach_a.id
