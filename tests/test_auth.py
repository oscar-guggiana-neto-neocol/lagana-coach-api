from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import security
from app.core.security import get_password_hash
from app.models.coach import Coach
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.enums import UserRole


def create_user_and_coach(db: Session, email: str = "coach@example.com", password: str = "password") -> Coach:
    user = User(email=email, hashed_password=get_password_hash(password), role=UserRole.coach, is_active=True)
    coach = Coach(full_name="Coach One", email=email, user=user, active=True)
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


def test_login_returns_tokens(client: TestClient, db_session: Session):
    create_user_and_coach(db_session)
    response = client.post("/api/v1/auth/login", json={"email": "coach@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_password_reset_flow(client: TestClient, db_session: Session):
    coach = create_user_and_coach(db_session, email="reset@example.com", password="oldpass")

    forgot_response = client.post("/api/v1/auth/password/forgot", json={"email": "reset@example.com"})
    assert forgot_response.status_code == 200

    token = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == coach.user.id).first()
    assert token is not None

    reset_response = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token.token, "new_password": "newpass"},
    )
    assert reset_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login", json={"email": "reset@example.com", "password": "newpass"}
    )
    assert login_response.status_code == 200



def test_register_coach_creates_user_and_coach(client: TestClient, db_session: Session):
    payload = {
        "full_name": "Coach Register",
        "email": "coach.register@example.com",
        "password": "secret",
        "city": "London",
        "country": "UK",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["detail"] == "Coach registered successfully"

    user = db_session.query(User).filter(User.email == payload["email"]).first()
    assert user is not None
    assert user.coach.full_name == payload["full_name"]
    assert user.coach.city == payload["city"]
    assert security.verify_password(payload["password"], user.hashed_password)
