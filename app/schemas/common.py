from typing import Generic, List, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int


class Message(GenericModel):
    detail: str
