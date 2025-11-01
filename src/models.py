from typing import Optional
from pydantic import BaseModel


class ListAccountsArgs(BaseModel):
    filter: Optional[str] = None
    tombstones: Optional[bool] = None
    cursor: Optional[str] = None


class GetAccountArgs(BaseModel):
    id: str


__all__ = ["ListAccountsArgs", "GetAccountArgs"]
