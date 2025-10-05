from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.stroke import Stroke
from app.models.user import User
from app.schemas.common import Message, PaginatedResponse
from app.schemas.stroke import StrokeCreate, StrokeRead, StrokeUpdate

router = APIRouter(prefix="/strokes", tags=["Strokes"])


@router.get("/", response_model=PaginatedResponse[StrokeRead])
def list_strokes(db: Session = Depends(get_db), page: int = 1, size: int = 20):
    query = db.query(Stroke)
    total = query.count()
    strokes = query.order_by(Stroke.label).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(items=strokes, total=total, page=page, size=size)


@router.post("/", response_model=StrokeRead, status_code=status.HTTP_201_CREATED)
def create_stroke(payload: StrokeCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stroke = Stroke(**payload.dict())
    db.add(stroke)
    db.commit()
    db.refresh(stroke)
    return stroke


@router.patch("/{stroke_id}", response_model=StrokeRead)
def update_stroke(
    stroke_id: int,
    payload: StrokeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    stroke = db.get(Stroke, stroke_id)
    if not stroke:
        raise HTTPException(status_code=404, detail="Stroke not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(stroke, field, value)
    db.commit()
    db.refresh(stroke)
    return stroke


@router.delete("/{stroke_id}", response_model=Message)
def delete_stroke(stroke_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stroke = db.get(Stroke, stroke_id)
    if not stroke:
        raise HTTPException(status_code=404, detail="Stroke not found")
    db.delete(stroke)
    db.commit()
    return Message(detail="Stroke deleted")
