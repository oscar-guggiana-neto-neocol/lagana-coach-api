from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_coach, get_current_user, require_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.coach import Coach
from app.models.user import User
from app.schemas.coach import CoachCreate, CoachRead, CoachUpdate
from app.schemas.common import Message, PaginatedResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/coaches", tags=["Coaches"])


@router.get("/", response_model=PaginatedResponse[CoachRead])
def list_coaches(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    page: int = 1,
    size: int = 20,
):
    query = db.query(Coach)
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
def get_my_profile(coach=Depends(get_current_coach)):
    return coach


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
    coach = db.get(Coach, coach_id)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(coach, field, value)

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
