from typing import Optional
from pydantic import BaseModel, Field

from src.pagination import DEFAULT_MAX_OBJECTS, MAX_OBJECTS_HARD_LIMIT


class ListAccountsArgs(BaseModel):
    filter: Optional[str] = None
    tombstones: Optional[bool] = None
    max_objects: int = Field(default=DEFAULT_MAX_OBJECTS, ge=1, le=MAX_OBJECTS_HARD_LIMIT)


class GetAccountArgs(BaseModel):
    id: str


class ListStorageCollectionsArgs(BaseModel):
    """No arguments required for listing collections (kept for symmetry)."""
    pass


class ListStorageArgs(BaseModel):
    collection: Optional[str] = None
    key: Optional[str] = None
    user_id: Optional[str] = None
    max_objects: int = Field(default=DEFAULT_MAX_OBJECTS, ge=1, le=MAX_OBJECTS_HARD_LIMIT)


class GetStorageObjectArgs(BaseModel):
    collection: str
    key: str
    user_id: str


__all__ = [
    "ListAccountsArgs",
    "GetAccountArgs",
    "ListStorageCollectionsArgs",
    "ListStorageArgs",
    "GetStorageObjectArgs",
]
