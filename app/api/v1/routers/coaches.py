from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.v1.dependencies import get_current_coach, get_current_user, require_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.coach import Coach
from app.models.club import Club
from app.models.user import User
from app.schemas.coach import CoachCreate, CoachRead, CoachUpdate, CoachSelfUpdate
from app.schemas.common import Message, PaginatedResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/coaches", tags=["Coaches"])


def _apply_club_memberships(
    db: Session,
    coach: Coach,
    club_ids: Optional[List[int]],
    default_club_id: Optional[int],
    *,
    restrict_to_current: bool = False,
) -> None:
    if club_ids is not None:
        unique_ids = list(dict.fromkeys(int(club_id) for club_id in club_ids))
        if restrict_to_current:
            current_ids = {club.id for club in coach.clubs}
            if not set(unique_ids).issubset(current_ids):
                raise HTTPException(status_code=403, detail="Cannot attach to unauthorized club")
            coach.clubs = [club for club in coach.clubs if club.id in unique_ids]
        else:
            if unique_ids:
                clubs = db.query(Club).filter(Club.id.in_(unique_ids)).all()
                if len(clubs) != len(unique_ids):
                    raise HTTPException(status_code=404, detail="One or more clubs not found")
                coach.clubs = clubs
            else:
                coach.clubs = []

    if default_club_id is not None:
        if default_club_id and default_club_id not in {club.id for club in coach.clubs}:
            raise HTTPException(status_code=400, detail="Default club must be among assigned clubs")
        coach.default_club_id = default_club_id


@router.get("/", response_model=PaginatedResponse[CoachRead])
def list_coaches(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    page: int = 1,
    size: int = 20,
):
    query = db.query(Coach).options(selectinload(Coach.clubs), selectinload(Coach.default_club), selectinload(Coach.user))
    total = query.count()
    coaches = query.offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=coaches, total=total, page=page, size=size)


@router.post("/", response_model=CoachRead, status_code=status.HTTP_201_CREATED)
def create_coach(
    payload: CoachCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.query(User).filter(User.email == payload.user_email).first():
        raise HTTPException(status_code=400, detail="User email already exists")

    user = User(
        email=payload.user_email,
        hashed_password=get_password_hash(payload.user_password),
        role=payload.user_role,
        is_active=True,
    )
    coach = Coach(
        user=user,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        postcode=payload.postcode,
        country=payload.country,
        bank_name=payload.bank_name,
        account_holder_name=payload.account_holder_name,
        sort_code=payload.sort_code,
        account_number=payload.account_number,
        iban=payload.iban,
        swift_bic=payload.swift_bic,
        hourly_rate=payload.hourly_rate,
        active=payload.active,
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.get("/me", response_model=CoachRead)
def get_my_profile(
    coach=Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    return (
        db.query(Coach)
        .options(
            selectinload(Coach.clubs).selectinload(Club.courts),
            selectinload(Coach.default_club),
            selectinload(Coach.user),
        )
        .filter(Coach.id == coach.id)
        .first()
    )


@router.get("/{coach_id}", response_model=CoachRead)
def get_coach(coach_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    coach = db.get(Coach, coach_id)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    return coach


@router.patch("/{coach_id}", response_model=CoachRead)
def update_coach(
    coach_id: int,
    payload: CoachUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    coach = db.query(Coach).options(selectinload(Coach.clubs)).filter(Coach.id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")

    data = payload.dict(exclude_unset=True)
    club_ids = data.pop("club_ids", None)
    default_club_id = data.pop("default_club_id", None)

    for field, value in data.items():
        setattr(coach, field, value)

    _apply_club_memberships(db, coach, club_ids, default_club_id)

    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.patch("/me", response_model=CoachRead)
def update_my_profile(
    payload: CoachSelfUpdate,
    current_coach=Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    coach = (
        db.query(Coach)
        .options(selectinload(Coach.clubs), selectinload(Coach.default_club), selectinload(Coach.user))
        .filter(Coach.id == current_coach.id)
        .first()
    )
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")

    data = payload.dict(exclude_unset=True)
    club_ids = data.pop("club_ids", None)
    default_club_id = data.pop("default_club_id", None)

    for field, value in data.items():
        setattr(coach, field, value)

    _apply_club_memberships(db, coach, club_ids, default_club_id, restrict_to_current=True)

    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.delete("/{coach_id}", response_model=Message)
def deactivate_coach(
    coach_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    coach = db.get(Coach, coach_id)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")
    coach.active = False
    coach.user.is_active = False
    db.commit()
    return Message(detail="Coach deactivated")
