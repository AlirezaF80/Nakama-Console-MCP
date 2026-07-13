from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.pagination import (
    DEFAULT_MAX_OBJECTS,
    MAX_BATCH_INPUT,
    MAX_OBJECTS_HARD_LIMIT,
)
from src.validation import key_prefix_to_filter, validate_storage_key_filter


class ListAccountsArgs(BaseModel):
    filter: Optional[str] = None
    tombstones: Optional[bool] = None
    max_objects: int = Field(default=DEFAULT_MAX_OBJECTS, ge=1, le=MAX_OBJECTS_HARD_LIMIT)


class GetAccountArgs(BaseModel):
    id: str


class ListStorageCollectionsArgs(BaseModel):
    """No arguments required for listing collections (kept for symmetry)."""
    pass


class StatusArgs(BaseModel):
    """No arguments required for server status."""
    pass


class ListStorageArgs(BaseModel):
    collection: Optional[str] = None
    key: Optional[str] = None
    user_id: Optional[str] = None
    max_objects: int = Field(default=DEFAULT_MAX_OBJECTS, ge=1, le=MAX_OBJECTS_HARD_LIMIT)

    @model_validator(mode="after")
    def validate_key_filters(self):
        if self.key is not None and self.collection is None:
            raise ValueError("collection is required when key is provided")
        if self.key is not None:
            self.key = validate_storage_key_filter(self.key)
        return self


class ListUserStorageArgs(BaseModel):
    user_id: str
    collection: Optional[str] = None
    key_prefix: Optional[str] = None
    max_objects: int = Field(default=DEFAULT_MAX_OBJECTS, ge=1, le=MAX_OBJECTS_HARD_LIMIT)

    @model_validator(mode="after")
    def validate_key_prefix(self):
        if self.key_prefix is not None:
            key_prefix_to_filter(self.key_prefix)
        return self


class ListStorageKeysArgs(BaseModel):
    collection: str
    user_id: Optional[str] = None
    key_prefix: Optional[str] = None
    max_objects: int = Field(default=DEFAULT_MAX_OBJECTS, ge=1, le=MAX_OBJECTS_HARD_LIMIT)

    @model_validator(mode="after")
    def validate_key_prefix(self):
        if self.key_prefix is not None:
            key_prefix_to_filter(self.key_prefix)
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
    objects: List[StorageObjectId] = Field(min_length=1, max_length=MAX_BATCH_INPUT)


# --- Response envelopes (MCP outputSchema) ---


class ListAccountsEnvelope(BaseModel):
    users: list[dict[str, Any]] = Field(description="Account user objects from Nakama")
    total_count: int = Field(description="Approximate total matching accounts")
    fetched: int = Field(description="Number of users returned in this response")
    complete: bool = Field(
        description="True if all matching users were returned within max_objects"
    )
    hint: Optional[str] = Field(
        default=None, description="Suggested next step or narrowing advice"
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
    hint: Optional[str] = Field(
        default=None, description="Suggested next step or narrowing advice"
    )


class ListStorageKeysEnvelope(BaseModel):
    keys: list[dict[str, str]] = Field(
        description="Storage object identities as {key, user_id} (collection is implicit)"
    )
    total_count: int = Field(description="Approximate total matching storage objects")
    fetched: int = Field(description="Number of keys returned in this response")
    complete: bool = Field(
        description="True if all matching keys were returned within max_objects"
    )
    hint: Optional[str] = Field(
        default=None, description="Suggested next step or narrowing advice"
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
    requested: int = Field(description="Number of object ids in the request")
    chunks: int = Field(description="Number of internal batches processed")
    fetched: int = Field(description="Count of successful fetches")
    failed: int = Field(description="Count of failed fetches")


class StatusEnvelope(BaseModel):
    console_url: str = Field(description="Nakama Console URL for this MCP connection")
    authenticated: bool = Field(description="Whether the MCP server has a valid session token")
    read_only: bool = Field(default=True, description="This MCP server is read-only")
    nodes: list[dict[str, Any]] = Field(
        default_factory=list, description="Node status from GET /v2/console/status"
    )
    timestamp: Optional[str] = Field(
        default=None, description="Status snapshot timestamp from Nakama when available"
    )
    hint: Optional[str] = Field(
        default=None, description="Connection or API notes when status is partial"
    )


class CollectionsEnvelope(BaseModel):
    collections: list[str] = Field(description="Storage collection names")


class StorageObjectEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    collection: Optional[str] = Field(default=None, description="Collection name")
    key: Optional[str] = Field(default=None, description="Storage object key")
    user_id: Optional[str] = Field(default=None, description="User/owner ID")
    value: Optional[Any] = Field(default=None, description="Decoded storage value when JSON")
    version: Optional[str] = Field(default=None, description="Object version hash")
    permission_read: Optional[int] = Field(default=None, description="Read permission level")
    permission_write: Optional[int] = Field(default=None, description="Write permission level")
    create_time: Optional[str] = Field(default=None, description="Creation timestamp")
    update_time: Optional[str] = Field(default=None, description="Last update timestamp")


class AccountEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    user: Optional[dict[str, Any]] = Field(default=None, description="User profile")
    wallet: Optional[Any] = Field(default=None, description="Wallet data")
    devices: Optional[list[dict[str, Any]]] = Field(default=None, description="Linked devices")
    custom_id: Optional[str] = Field(default=None, description="Custom account id")
    disable_time: Optional[str] = Field(default=None, description="Disable timestamp if banned")


class ExportAccountEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    account: Optional[dict[str, Any]] = Field(default=None, description="Account record")
    storage: Optional[list[dict[str, Any]]] = Field(default=None, description="Storage objects")
    friends: Optional[list[dict[str, Any]]] = Field(default=None, description="Friends")
    groups: Optional[list[dict[str, Any]]] = Field(default=None, description="Groups")
    messages: Optional[list[dict[str, Any]]] = Field(default=None, description="Messages")
    notifications: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Notifications"
    )
    leaderboard_records: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Leaderboard records"
    )
    wallet_ledger: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Wallet ledger entries"
    )


class FriendsEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    friends: Optional[list[dict[str, Any]]] = Field(default=None, description="Friend entries")
    cursor: Optional[str] = Field(default=None, description="Pagination cursor when present")


class UserGroupsEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    groups: Optional[list[dict[str, Any]]] = Field(default=None, description="Group memberships")
    cursor: Optional[str] = Field(default=None, description="Pagination cursor when present")


__all__ = [
    "ListAccountsArgs",
    "GetAccountArgs",
    "ListStorageCollectionsArgs",
    "StatusArgs",
    "ListStorageArgs",
    "ListUserStorageArgs",
    "ListStorageKeysArgs",
    "GetStorageObjectArgs",
    "StorageObjectId",
    "GetStorageObjectsArgs",
    "ListAccountsEnvelope",
    "ListStorageEnvelope",
    "ListStorageKeysEnvelope",
    "StorageBatchResultItem",
    "GetStorageObjectsEnvelope",
    "StatusEnvelope",
    "CollectionsEnvelope",
    "StorageObjectEnvelope",
    "AccountEnvelope",
    "ExportAccountEnvelope",
    "FriendsEnvelope",
    "UserGroupsEnvelope",
]
