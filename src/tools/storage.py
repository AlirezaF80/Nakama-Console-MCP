from typing import Optional
import json
from urllib.parse import quote

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
        key: Filter by key (supports % suffix for prefix search, e.g., 'level%') (Optional, but collection is required if key is provided)
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

    Returns the full storage object (matching the console REST shape) and
    attempts to JSON-decode the "value" field when it's a JSON string.
    """

    # The console exposes a convenience endpoint:
    # /v2/console/storage/{collection}/{key}/{user_id}
    # Make sure each segment is URL-encoded so unusual characters work.
    def _encode(segment: str) -> str:
        return quote(segment, safe="")

    path = "/v2/console/storage/{}/{}/{}".format(
        _encode(collection), _encode(key), _encode(user_id)
    )

    obj = await client.get(path)

    # If the storage object's value is a JSON-encoded string, parse it for convenience.
    value = obj.get("value") if isinstance(obj, dict) else None
    if isinstance(value, str):
        try:
            obj["value"] = json.loads(value)
        except Exception:
            # leave as string if not JSON
            pass

    return obj


__all__ = [
    "nakama_list_collections",
    "nakama_list_storage",
    "nakama_get_storage_object",
]
