from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, resolve_coach
from app.db.session import get_db
from app.models.enums import LessonPaymentStatus, LessonStatus, UserRole
from app.models.lesson import Lesson
from app.models.player import Player
from app.models.stroke import Stroke
from app.models.user import User
from app.schemas.common import Message, PaginatedResponse
from app.schemas.lesson import LessonCreate, LessonRead, LessonUpdate
from app.utils.time import calculate_duration_minutes

router = APIRouter(prefix="/lessons", tags=["Lessons"])


def _scoped_query(db: Session, user: User):
    query = db.query(Lesson)
    if user.role == UserRole.coach:
        coach = resolve_coach(current_user=user, db=db)
        query = query.filter(Lesson.coach_id == coach.id)
    return query


def _ensure_player_visibility(db: Session, user: User, player_ids: List[int]) -> List[Player]:
    players = db.query(Player).filter(Player.id.in_(player_ids)).all()
    if len(players) != len(set(player_ids)):
        raise HTTPException(status_code=400, detail="One or more players not found")
    if user.role == UserRole.coach:
        coach = resolve_coach(current_user=user, db=db)
        for player in players:
            if coach not in player.coaches:
                raise HTTPException(status_code=403, detail="Cannot attach unassigned player")
    return players


def _get_strokes(db: Session, stroke_codes: List[str]) -> List[Stroke]:
    if not stroke_codes:
        return []
    strokes = db.query(Stroke).filter(Stroke.code.in_(stroke_codes)).all()
    if len(strokes) != len(set(stroke_codes)):
        raise HTTPException(status_code=400, detail="One or more strokes not found")
    return strokes


@router.get("/", response_model=PaginatedResponse[LessonRead])
def list_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    status_filter: Optional[LessonStatus] = Query(default=None, alias="status"),
    payment_status: Optional[LessonPaymentStatus] = Query(default=None),
    club_id: Optional[int] = Query(default=None),
    player_id: Optional[int] = Query(default=None),
):
    query = _scoped_query(db, current_user)

    if date_from:
        query = query.filter(Lesson.date >= date_from)
    if date_to:
        query = query.filter(Lesson.date <= date_to)
    if status_filter:
        query = query.filter(Lesson.status == status_filter)
    if payment_status:
        query = query.filter(Lesson.payment_status == payment_status)
    if club_id:
        query = query.filter(Lesson.club_id == club_id)
    if player_id:
        query = query.join(Lesson.players).filter(Player.id == player_id)

    total = query.count()
    lessons = (
        query.order_by(Lesson.date.desc(), Lesson.start_time.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return PaginatedResponse(items=lessons, total=total, page=page, size=size)


@router.post("/", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    coach_id = payload.coach_id
    if current_user.role == UserRole.coach:
        coach_id = resolve_coach(current_user=current_user, db=db).id

    duration = calculate_duration_minutes(payload.start_time, payload.end_time)

    reimbursement = payload.club_reimbursement_amount
    if reimbursement is not None:
        reimbursement = abs(reimbursement)

    lesson = Lesson(
        coach_id=coach_id,
        club_id=payload.club_id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_minutes=duration,
        total_amount=payload.total_amount,
        type=payload.type,
        status=payload.status,
        payment_status=payload.payment_status,
        club_reimbursement_amount=reimbursement,
        notes=payload.notes,
    )
    db.add(lesson)
    db.flush()

    lesson.players = _ensure_player_visibility(db, current_user, payload.player_ids)
    lesson.strokes = _get_strokes(db, [code.value for code in payload.stroke_codes])

    db.commit()
    db.refresh(lesson)
    return lesson


@router.get("/{lesson_id}", response_model=LessonRead)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if current_user.role == UserRole.coach and lesson.coach_id != resolve_coach(current_user=current_user, db=db).id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return lesson


@router.patch("/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if current_user.role == UserRole.coach and lesson.coach_id != resolve_coach(current_user=current_user, db=db).id:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = payload.dict(exclude_unset=True)
    player_ids = data.pop("player_ids", None)
    stroke_codes = data.pop("stroke_codes", None)

    start_time = data.get("start_time", lesson.start_time)
    end_time = data.get("end_time", lesson.end_time)
    if "start_time" in data or "end_time" in data:
        lesson.duration_minutes = calculate_duration_minutes(start_time, end_time)

    if "club_reimbursement_amount" in data and data["club_reimbursement_amount"] is not None:
        data["club_reimbursement_amount"] = abs(data["club_reimbursement_amount"])

    for field, value in data.items():
        setattr(lesson, field, value)

    if player_ids is not None:
        lesson.players = _ensure_player_visibility(db, current_user, player_ids)
    if stroke_codes is not None:
        stroke_values = [code.value if hasattr(code, "value") else code for code in stroke_codes]
        lesson.strokes = _get_strokes(db, stroke_values)

    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", response_model=Message)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if current_user.role == UserRole.coach and lesson.coach_id != resolve_coach(current_user=current_user, db=db).id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(lesson)
    db.commit()
    return Message(detail="Lesson deleted")
