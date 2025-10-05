from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core import security
from app.db.session import get_db
from app.models.coach import Coach
from app.models.enums import UserRole
from app.models.user import User


async def get_token_from_request(
    request: Request, authorization: Optional[str] = Header(default=None)
) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split()[1]

    token = request.cookies.get("access_token")
    if token:
        return token
    return None


def get_current_user(
    db: Session = Depends(get_db), token: Optional[str] = Depends(get_token_from_request)
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = security.decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


def require_coach(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.coach, UserRole.admin}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach privileges required")
    return current_user


def resolve_coach(current_user: User, db: Session) -> Coach:
    if current_user.role != UserRole.coach:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a coach")
    coach = (
        db.query(Coach)
        .filter(Coach.user_id == current_user.id, Coach.active.is_(True))
        .first()
    )
    if not coach:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coach profile not found")
    return coach


def get_current_coach(
    current_user: User = Depends(require_coach), db: Session = Depends(get_db)
) -> Coach:
    if current_user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin is not a coach")
    return resolve_coach(current_user=current_user, db=db)
