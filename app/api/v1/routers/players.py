from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, resolve_coach
from app.db.session import get_db
from app.models.coach import Coach
from app.models.player import Player
from app.models.associations import player_coach_table
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import Message, PaginatedResponse
from app.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate

router = APIRouter(prefix="/players", tags=["Players"])


def _apply_coach_scope(query, coach: Coach):
    return query.join(player_coach_table).filter(player_coach_table.c.coach_id == coach.id)


@router.get("/", response_model=PaginatedResponse[PlayerRead])
def list_players(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: Optional[str] = Query(default=None, description="Filter by player name"),
):
    query = db.query(Player)
    if search:
        query = query.filter(Player.full_name.ilike(f"%{search}%"))

    if current_user.role == UserRole.coach:
        coach = resolve_coach(current_user=current_user, db=db)
        query = _apply_coach_scope(query, coach)

    total = query.count()
    players = query.order_by(Player.full_name).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=players, total=total, page=page, size=size)


@router.post("/", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
def create_player(
    payload: PlayerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    coach_ids = payload.coach_ids
    if current_user.role == UserRole.coach:
        coach = resolve_coach(current_user=current_user, db=db)
        coach_ids = [coach.id]

    coaches = db.query(Coach).filter(Coach.id.in_(coach_ids)).all()
    if len(coaches) != len(set(coach_ids)):
        raise HTTPException(status_code=400, detail="One or more coaches not found")

    player = Player(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        birth_date=payload.birth_date,
        skill_level=payload.skill_level,
        notes=payload.notes,
        active=payload.active,
        coaches=coaches,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def _check_player_access(player: Player, current_user: User, db: Session) -> None:
    if current_user.role == UserRole.admin:
        return
    coach = resolve_coach(current_user=current_user, db=db)
    if coach not in player.coaches:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/{player_id}", response_model=PlayerRead)
def get_player(player_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    _check_player_access(player, current_user, db)
    return player


@router.patch("/{player_id}", response_model=PlayerRead)
def update_player(
    player_id: int,
    payload: PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    _check_player_access(player, current_user, db)

    data = payload.dict(exclude_unset=True)
    coach_ids = data.pop("coach_ids", None)
    for field, value in data.items():
        setattr(player, field, value)

    if coach_ids is not None:
        if current_user.role == UserRole.coach:
            coach = resolve_coach(current_user=current_user, db=db)
            coach_ids = [coach.id]
        coaches = db.query(Coach).filter(Coach.id.in_(coach_ids)).all()
        player.coaches = coaches

    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.delete("/{player_id}", response_model=Message)
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    _check_player_access(player, current_user, db)
    player.active = False
    db.add(player)
    db.commit()
    return Message(detail="Player archived")
