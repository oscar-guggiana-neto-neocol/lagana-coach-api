from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.club import Club
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.club import ClubCreate, ClubRead, ClubUpdate
from app.schemas.common import Message, PaginatedResponse

router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.get("/", response_model=PaginatedResponse[ClubRead])
def list_clubs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
):
    query = db.query(Club)
    total = query.count()
    clubs = query.order_by(Club.name).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=clubs, total=total, page=page, size=size)


@router.post("/", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club(
    payload: ClubCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    club = Club(**payload.dict())
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


@router.get("/{club_id}", response_model=ClubRead)
def get_club(club_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.patch("/{club_id}", response_model=ClubRead)
def update_club(
    club_id: int,
    payload: ClubUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(club, field, value)
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


@router.delete("/{club_id}", response_model=Message)
def delete_club(club_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    db.delete(club)
    db.commit()
    return Message(detail="Club deleted")
