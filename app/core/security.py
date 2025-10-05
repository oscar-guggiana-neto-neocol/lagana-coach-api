from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

import os

os.environ.setdefault("PASSLIB_BCRYPT_NO_CHECK", "1")

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """Raised when a token cannot be validated."""


def create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": now + expires_delta,
        "iat": now,
        "type": token_type,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    expires = timedelta(minutes=settings.jwt_access_expires_min)
    return create_token(subject, expires, token_type="access")


def create_refresh_token(subject: str) -> str:
    expires = timedelta(minutes=settings.jwt_refresh_expires_min)
    return create_token(subject, expires, token_type="refresh")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AuthenticationError("Could not validate credentials") from exc

    if payload.get("type") != expected_type:
        raise AuthenticationError("Invalid token type")
    return payload
