from typing import Optional
from pydantic import BaseModel


class ListAccountsArgs(BaseModel):
    filter: Optional[str] = None
    tombstones: Optional[bool] = None
    cursor: Optional[str] = None


class GetAccountArgs(BaseModel):
    id: str



class ListStorageCollectionsArgs(BaseModel):
    """No arguments required for listing collections (kept for symmetry)."""
    pass


class ListStorageArgs(BaseModel):
    collection: Optional[str] = None
    key: Optional[str] = None
    user_id: Optional[str] = None
    cursor: Optional[str] = None


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
