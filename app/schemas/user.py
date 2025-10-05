from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.coach
    is_active: bool = True


class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True
