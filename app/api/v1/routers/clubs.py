from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.v1.dependencies import get_current_user, require_coach
from app.db.session import get_db
from app.models.club import Club
from app.models.coach import Coach
from app.models.court import Court
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.club import ClubCreate, ClubRead, ClubUpdate
from app.schemas.court import CourtCreate, CourtRead, CourtUpdate
from app.schemas.common import Message, PaginatedResponse

router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.get("/", response_model=PaginatedResponse[ClubRead])
def list_clubs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
):
    query = db.query(Club).options(selectinload(Club.courts))
    if current_user.role == UserRole.coach:
        coach = current_user.coach
        if not coach:
            return PaginatedResponse(items=[], total=0, page=page, size=size)
        query = (
            query.join(Club.coaches)
            .filter(Coach.id == coach.id)
            .options(selectinload(Club.courts))
        )
    total = query.count()
    clubs = query.order_by(Club.name).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=clubs, total=total, page=page, size=size)


@router.post("/", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club(
    payload: ClubCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    club = Club(**payload.dict())
    db.add(club)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Club with this name already exists") from exc
    db.refresh(club)

    if current_user.role == UserRole.coach:
        coach = current_user.coach
        if coach:
            if club not in coach.clubs:
                coach.clubs.append(club)
            if coach.default_club_id is None:
                coach.default_club = club
            db.add(coach)
            db.commit()
            db.refresh(club)
    return club


@router.get("/{club_id}", response_model=ClubRead)
def get_club(club_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    club = (
        db.query(Club)
        .options(selectinload(Club.courts))
        .filter(Club.id == club_id)
        .first()
    )
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.patch("/{club_id}", response_model=ClubRead)
def update_club(
    club_id: int,
    payload: ClubUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_coach),
):
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(club, field, value)
    db.add(club)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Club with this name already exists") from exc
    db.refresh(club)
    return club


@router.delete("/{club_id}", response_model=Message)
def delete_club(club_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_coach)):
    club = _get_club_with_permission(db, club_id, current_user)
    for coach in list(club.coaches):
        if coach.default_club_id == club.id:
            coach.default_club = None
        coach.clubs = [c for c in coach.clubs if c.id != club.id]
        db.add(coach)

    db.delete(club)
    db.commit()
    return Message(detail="Club deleted")


def _get_club_with_permission(db: Session, club_id: int, current_user: User) -> Club:
    club = db.query(Club).options(selectinload(Club.coaches)).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if current_user.role == UserRole.coach:
        coach = current_user.coach
        if not coach or club not in coach.clubs:
            raise HTTPException(status_code=403, detail="Coach cannot access this club")
    return club


def _get_court(db: Session, club_id: int, court_id: int) -> Court:
    court = db.query(Court).filter(Court.id == court_id, Court.club_id == club_id).first()
    if not court:
        raise HTTPException(status_code=404, detail="Court not found")
    return court


@router.post("/{club_id}/courts", response_model=CourtRead, status_code=status.HTTP_201_CREATED)
def create_court(
    club_id: int,
    payload: CourtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    _get_club_with_permission(db, club_id, current_user)
    existing = (
        db.query(Court)
        .filter(Court.club_id == club_id, Court.name.ilike(payload.name))
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Court with this name already exists for the club")

    court = Court(club_id=club_id, name=payload.name, active=payload.active)
    db.add(court)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Court with this name already exists for the club") from exc
    db.refresh(court)
    return court


@router.patch("/{club_id}/courts/{court_id}", response_model=CourtRead)
def update_court(
    club_id: int,
    court_id: int,
    payload: CourtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    _get_club_with_permission(db, club_id, current_user)
    court = _get_court(db, club_id, court_id)
    data = payload.dict(exclude_unset=True)
    if "name" in data:
        existing = (
            db.query(Court)
            .filter(Court.club_id == club_id, Court.name.ilike(data["name"]), Court.id != court_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Court with this name already exists for the club")

    for field, value in data.items():
        setattr(court, field, value)

    db.add(court)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Court with this name already exists for the club") from exc
    db.refresh(court)
    return court


@router.delete("/{club_id}/courts/{court_id}", response_model=Message)
def delete_court(
    club_id: int,
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    _get_club_with_permission(db, club_id, current_user)
    court = _get_court(db, club_id, court_id)
    db.delete(court)
    db.commit()
    return Message(detail="Court deleted")
