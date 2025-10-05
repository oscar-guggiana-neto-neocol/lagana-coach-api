from typing import Optional

from pydantic import BaseModel

from app.models.enums import StrokeCode


class StrokeBase(BaseModel):
    code: StrokeCode
    label: str


class StrokeCreate(StrokeBase):
    pass


class StrokeUpdate(BaseModel):
    label: Optional[str] = None


class StrokeRead(StrokeBase):
    id: int

    class Config:
        orm_mode = True
