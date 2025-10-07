from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole
from app.schemas.club import ClubRead
from app.schemas.user import UserRead


class CoachBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    sort_code: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    swift_bic: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    active: bool = True


class CoachCreate(CoachBase):
    user_email: EmailStr
    user_password: str
    user_role: UserRole = UserRole.coach


class CoachUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    sort_code: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    swift_bic: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    active: Optional[bool] = None
    club_ids: Optional[List[int]] = None
    default_club_id: Optional[int] = None


class CoachSelfUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    sort_code: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    swift_bic: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    club_ids: Optional[List[int]] = None
    default_club_id: Optional[int] = None


class CoachRead(CoachBase):
    id: int
    user: UserRead
    default_club_id: Optional[int] = None
    clubs: List[ClubRead] = []

    class Config:
        orm_mode = True


class CoachSimple(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        orm_mode = True
