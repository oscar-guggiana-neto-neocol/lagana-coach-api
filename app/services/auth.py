from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core import security
from app.models.user import User


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def create_access_and_refresh_tokens(user: User) -> Tuple[str, str]:
    subject = str(user.id)
    access = security.create_access_token(subject)
    refresh = security.create_refresh_token(subject)
    return access, refresh
