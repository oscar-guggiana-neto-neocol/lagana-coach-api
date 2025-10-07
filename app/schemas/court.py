from typing import Optional

from pydantic import BaseModel


class CourtBase(BaseModel):
    name: str
    active: bool = True


class CourtCreate(CourtBase):
    pass


class CourtUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class CourtRead(CourtBase):
    id: int

    class Config:
        orm_mode = True
