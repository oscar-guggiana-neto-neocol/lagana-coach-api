from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import SkillLevel
from app.schemas.coach import CoachSimple


class PlayerBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skill_level: SkillLevel = SkillLevel.beginner
    notes: Optional[str] = None
    active: bool = True


class PlayerCreate(PlayerBase):
    coach_ids: List[int]


class PlayerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    skill_level: Optional[SkillLevel] = None
    notes: Optional[str] = None
    active: Optional[bool] = None
    coach_ids: Optional[List[int]] = None


class PlayerRead(PlayerBase):
    id: int
    coaches: List[CoachSimple]

    class Config:
        orm_mode = True
