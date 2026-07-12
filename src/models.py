from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator

from src.pagination import DEFAULT_MAX_OBJECTS, MAX_BATCH_OBJECTS, MAX_OBJECTS_HARD_LIMIT


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

    @model_validator(mode="after")
    def key_requires_collection(self):
        if self.key is not None and self.collection is None:
            raise ValueError("collection is required when key is provided")
        return self


class GetStorageObjectArgs(BaseModel):
    collection: str
    key: str
    user_id: str


class StorageObjectId(BaseModel):
    collection: str
    key: str
    user_id: str


class GetStorageObjectsArgs(BaseModel):
    objects: List[StorageObjectId] = Field(min_length=1, max_length=MAX_BATCH_OBJECTS)


# --- Response envelopes (MCP outputSchema) ---


class ListAccountsEnvelope(BaseModel):
    users: list[dict[str, Any]] = Field(description="Account user objects from Nakama")
    total_count: int = Field(description="Approximate total matching accounts")
    fetched: int = Field(description="Number of users returned in this response")
    complete: bool = Field(
        description="True if all matching users were returned within max_objects"
    )


class ListStorageEnvelope(BaseModel):
    objects: list[dict[str, Any]] = Field(
        description="Storage object metadata only (no values)"
    )
    total_count: int = Field(description="Approximate total matching storage objects")
    fetched: int = Field(description="Number of objects returned in this response")
    complete: bool = Field(
        description="True if all matching objects were returned within max_objects"
    )


class StorageBatchResultItem(BaseModel):
    collection: str = Field(description="Collection name")
    key: str = Field(description="Storage object key")
    user_id: str = Field(description="User/owner ID")
    ok: bool = Field(description="True if the object was fetched successfully")
    object: Optional[dict[str, Any]] = Field(
        default=None, description="Full storage object when ok is true"
    )
    error: Optional[str] = Field(
        default=None, description="Error message when ok is false"
    )


class GetStorageObjectsEnvelope(BaseModel):
    results: list[StorageBatchResultItem] = Field(
        description="Per-item results in input order"
    )
    fetched: int = Field(description="Count of successful fetches")
    failed: int = Field(description="Count of failed fetches")


__all__ = [
    "ListAccountsArgs",
    "GetAccountArgs",
    "ListStorageCollectionsArgs",
    "ListStorageArgs",
    "GetStorageObjectArgs",
    "StorageObjectId",
    "GetStorageObjectsArgs",
    "ListAccountsEnvelope",
    "ListStorageEnvelope",
    "StorageBatchResultItem",
    "GetStorageObjectsEnvelope",
]
