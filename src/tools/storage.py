from typing import Optional

from src.nakama_client import NakamaConsoleClient


async def nakama_list_collections(client: NakamaConsoleClient):
    """List all storage collection names.

    Returns a list of collection names that exist in the storage system.
    """
    return await client.get("/v2/console/storage/collections")


async def nakama_list_storage(
    client: NakamaConsoleClient,
    collection: Optional[str] = None,
    key: Optional[str] = None,
    user_id: Optional[str] = None,
    cursor: Optional[str] = None,
):
    """List storage objects with optional filtering and pagination.

    Parameters:
        collection: Filter by collection name
        key: Filter by key (supports % suffix for prefix search, e.g., 'level%')
        user_id: Filter by user/owner ID
        cursor: Pagination cursor from previous response

    Returns storage objects with metadata (collection, key, user_id, version,
    permissions, timestamps) and a next_cursor for pagination.
    """
    params = {}
    if collection is not None:
        params["collection"] = collection
    if key is not None:
        params["key"] = key
    if user_id is not None:
        params["user_id"] = user_id
    if cursor is not None:
        params["cursor"] = cursor
    return await client.get("/v2/console/storage", params=params)


async def nakama_get_storage_object(
    client: NakamaConsoleClient, collection: str, key: str, user_id: str
):
    """Get a specific storage object by collection, key, and user_id.

    Returns the full storage object including the JSON value content.
    """
    params = {"collection": collection, "key": key, "user_id": user_id}
    return await client.get("/v2/console/storage", params=params)


__all__ = [
    "nakama_list_collections",
    "nakama_list_storage",
    "nakama_get_storage_object",
]
