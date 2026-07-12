from typing import Any, Dict, List, Optional, Sequence
import asyncio
import json
from urllib.parse import quote

from src.nakama_client import NakamaConsoleClient
from src.pagination import DEFAULT_MAX_OBJECTS, fetch_pages

MAX_BATCH_OBJECTS = 50
BATCH_CONCURRENCY = 10


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
    max_objects: int = DEFAULT_MAX_OBJECTS,
):
    """List storage objects with optional filtering; auto-paginates up to max_objects.

    Parameters:
        collection: Filter by collection name
        key: Filter by key (supports % suffix for prefix search, e.g., 'level%')
            (Optional, but collection is required if key is provided)
        user_id: Filter by user/owner ID
        max_objects: Max objects to return (default 100, hard max 1000)

    Returns an envelope with objects (metadata only), total_count (approximate),
    fetched, and complete. Raise max_objects or narrow filters if complete is false.
    """

    async def fetch_page(cursor: Optional[str]):
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

    return await fetch_pages(fetch_page, items_key="objects", max_objects=max_objects)


def _encode_path_segment(segment: str) -> str:
    return quote(segment, safe="")


def _decode_storage_value(obj: Any) -> Any:
    """JSON-decode the storage object's value field when it is a JSON string."""
    value = obj.get("value") if isinstance(obj, dict) else None
    if isinstance(value, str):
        try:
            obj["value"] = json.loads(value)
        except Exception:
            pass
    return obj


async def _get_storage_object(
    client: NakamaConsoleClient, collection: str, key: str, user_id: str
) -> Any:
    """GET one storage object and decode JSON value when applicable."""
    path = "/v2/console/storage/{}/{}/{}".format(
        _encode_path_segment(collection),
        _encode_path_segment(key),
        _encode_path_segment(user_id),
    )
    obj = await client.get(path)
    return _decode_storage_value(obj)


async def nakama_get_storage_object(
    client: NakamaConsoleClient, collection: str, key: str, user_id: str
):
    """Get a specific storage object by collection, key, and user_id.

    Returns the full storage object (matching the console REST shape) and
    attempts to JSON-decode the "value" field when it's a JSON string.
    """
    return await _get_storage_object(client, collection, key, user_id)


async def nakama_get_storage_objects(
    client: NakamaConsoleClient,
    objects: Sequence[Dict[str, str]],
):
    """Fetch multiple storage objects concurrently (max 50).

    Each entry must include collection, key, and user_id. Results stay in input
    order. Per-item failures do not abort the batch.

    Returns { results, fetched, failed }.
    """
    # Batch size / non-empty checks are enforced by GetStorageObjectsArgs in the dispatcher.
    semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)

    async def fetch_one(item: Dict[str, str]) -> Dict[str, Any]:
        collection = item.get("collection", "")
        key = item.get("key", "")
        user_id = item.get("user_id", "")
        base = {"collection": collection, "key": key, "user_id": user_id}
        try:
            async with semaphore:
                obj = await _get_storage_object(client, collection, key, user_id)
            return {**base, "ok": True, "object": obj}
        except Exception as e:
            return {**base, "ok": False, "error": str(e)}

    results = list(await asyncio.gather(*(fetch_one(item) for item in objects)))
    fetched = sum(1 for r in results if r.get("ok"))
    failed = len(results) - fetched
    return {"results": results, "fetched": fetched, "failed": failed}


__all__ = [
    "MAX_BATCH_OBJECTS",
    "nakama_list_collections",
    "nakama_list_storage",
    "nakama_get_storage_object",
    "nakama_get_storage_objects",
]
