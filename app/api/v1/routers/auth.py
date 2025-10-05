from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.coach import Coach
from app.models.enums import UserRole
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    RefreshRequest,
    CoachRegisterRequest,
)
from app.schemas.common import Message
from app.schemas.user import UserRead
from app.services import auth as auth_service
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"])

COOKIE_SETTINGS = {
    "httponly": True,
    "secure": not settings.debug,
    "samesite": "lax",
}


@router.post("/register", response_model=Message, status_code=status.HTTP_201_CREATED)
def register_coach(payload: CoachRegisterRequest, db: Session = Depends(get_db)) -> Message:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    coach_payload = payload.dict()
    password = coach_payload.pop("password")
    email = coach_payload.pop("email")
    user = User(
        email=email,
        hashed_password=security.get_password_hash(password),
        role=UserRole.coach,
        is_active=True,
    )
    coach = Coach(user=user, email=email, **coach_payload)
    db.add(coach)
    db.commit()
    return Message(detail="Coach registered successfully")


@router.post("/login", response_model=TokenResponse)
def login(  # type: ignore[override]
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = auth_service.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    access, refresh = auth_service.create_access_and_refresh_tokens(user)
    response.set_cookie("access_token", access, max_age=settings.jwt_access_expires_min * 60, **COOKIE_SETTINGS)
    response.set_cookie(
        "refresh_token",
        refresh,
        max_age=settings.jwt_refresh_expires_min * 60,
        **COOKIE_SETTINGS,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    refresh_payload = security.decode_token(payload.refresh_token, expected_type="refresh")
    user_id = refresh_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access, refresh = auth_service.create_access_and_refresh_tokens(user)
    response.set_cookie("access_token", access, max_age=settings.jwt_access_expires_min * 60, **COOKIE_SETTINGS)
    response.set_cookie(
        "refresh_token",
        refresh,
        max_age=settings.jwt_refresh_expires_min * 60,
        **COOKIE_SETTINGS,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", response_model=Message)
def logout(response: Response) -> Message:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return Message(detail="Logged out")


@router.post("/password/forgot", response_model=Message)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> Message:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        return Message(detail="If the email exists we sent a reset link")

    token_value = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_exp_minutes)

    reset = PasswordResetToken(
        user=user,
        token=token_value,
        expires_at=expires_at,
    )
    db.add(reset)
    db.commit()

    reset_link = f"{settings.frontend_base_url}/reset-password?token={token_value}"
    full_name = user.coach.full_name if user.coach else user.email
    send_password_reset_email(user.email, reset_link, full_name)

    return Message(detail="If the email exists we sent a reset link")


@router.post("/password/reset", response_model=Message)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> Message:
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == payload.token, PasswordResetToken.used.is_(False))
        .first()
    )
    if not reset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    now = datetime.now(timezone.utc)
    expires_at = reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

    user = reset.user
    user.hashed_password = security.get_password_hash(payload.new_password)
    reset.used = True

    db.add_all([user, reset])
    db.commit()

    return Message(detail="Password reset successful")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user=Depends(get_current_user)):
    return current_user
