from typing import Any, Dict, List, Optional, Sequence
import asyncio
import json
from urllib.parse import quote

from src.hints import append_hint, build_list_hint
from src.nakama_client import NakamaConsoleClient
from src.pagination import DEFAULT_MAX_OBJECTS, MAX_BATCH_OBJECTS, fetch_pages
from src.validation import key_prefix_to_filter

BATCH_CONCURRENCY = 10


async def nakama_list_collections(client: NakamaConsoleClient):
    """List all storage collection names.

    Returns a list of collection names that exist in the storage system.
    """
    return await client.get("/v2/console/storage/collections")


def _attach_storage_hint(
    envelope: Dict[str, Any],
    *,
    collection: Optional[str],
    key: Optional[str],
    user_id: Optional[str],
    key_prefix: Optional[str] = None,
    extra_hint: Optional[str] = None,
) -> Dict[str, Any]:
    hint = build_list_hint(
        complete=envelope.get("complete", True),
        fetched=envelope.get("fetched", 0),
        total_count=envelope.get("total_count", 0),
        filters={
            "collection": collection,
            "key": key,
            "key_prefix": key_prefix,
            "user_id": user_id,
        },
    )
    envelope["hint"] = append_hint(hint, extra_hint)
    return envelope


async def nakama_list_storage(
    client: NakamaConsoleClient,
    collection: Optional[str] = None,
    key: Optional[str] = None,
    user_id: Optional[str] = None,
    max_objects: int = DEFAULT_MAX_OBJECTS,
):
    """List storage objects with optional filtering; auto-paginates up to max_objects."""

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

    envelope = await fetch_pages(fetch_page, items_key="objects", max_objects=max_objects)
    return _attach_storage_hint(
        envelope,
        collection=collection,
        key=key,
        user_id=user_id,
    )


async def nakama_list_user_storage(
    client: NakamaConsoleClient,
    user_id: str,
    collection: Optional[str] = None,
    key_prefix: Optional[str] = None,
    max_objects: int = DEFAULT_MAX_OBJECTS,
):
    """List storage objects for a specific user with optional collection and key prefix."""
    key = key_prefix_to_filter(key_prefix)
    envelope = await nakama_list_storage(
        client,
        collection=collection,
        key=key,
        user_id=user_id,
        max_objects=max_objects,
    )
    extra = None
    if collection is None:
        extra = "Add collection to narrow results when many objects exist."
    return _attach_storage_hint(
        envelope,
        collection=collection,
        key=key,
        user_id=user_id,
        key_prefix=key_prefix,
        extra_hint=extra,
    )


async def nakama_list_storage_keys(
    client: NakamaConsoleClient,
    collection: str,
    user_id: Optional[str] = None,
    key_prefix: Optional[str] = None,
    max_objects: int = DEFAULT_MAX_OBJECTS,
):
    """List storage keys (metadata only) for a collection with optional filters."""
    key = key_prefix_to_filter(key_prefix)
    envelope = await nakama_list_storage(
        client,
        collection=collection,
        key=key,
        user_id=user_id,
        max_objects=max_objects,
    )

    keys = [
        {"key": obj.get("key", ""), "user_id": obj.get("user_id", "")}
        for obj in envelope.get("objects", [])
        if isinstance(obj, dict)
    ]

    result = {
        "keys": keys,
        "total_count": envelope.get("total_count", 0),
        "fetched": envelope.get("fetched", len(keys)),
        "complete": envelope.get("complete", True),
    }
    return _attach_storage_hint(
        result,
        collection=collection,
        key=key,
        user_id=user_id,
        key_prefix=key_prefix,
    )


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
    """Get a specific storage object by collection, key, and user_id."""
    return await _get_storage_object(client, collection, key, user_id)


async def _fetch_storage_batch(
    client: NakamaConsoleClient,
    objects: Sequence[Dict[str, str]],
) -> List[Dict[str, Any]]:
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

    return list(await asyncio.gather(*(fetch_one(item) for item in objects)))


async def nakama_get_storage_objects(
    client: NakamaConsoleClient,
    objects: Sequence[Dict[str, str]],
):
    """Fetch multiple storage objects concurrently with internal chunking."""
    requested = len(objects)
    if requested == 0:
        return {"results": [], "requested": 0, "chunks": 0, "fetched": 0, "failed": 0}

    chunks: List[List[Dict[str, str]]] = [
        list(objects[i : i + MAX_BATCH_OBJECTS])
        for i in range(0, requested, MAX_BATCH_OBJECTS)
    ]

    results: List[Dict[str, Any]] = []
    for chunk in chunks:
        results.extend(await _fetch_storage_batch(client, chunk))

    fetched = sum(1 for r in results if r.get("ok"))
    failed = len(results) - fetched
    return {
        "results": results,
        "requested": requested,
        "chunks": len(chunks),
        "fetched": fetched,
        "failed": failed,
    }


__all__ = [
    "MAX_BATCH_OBJECTS",
    "nakama_list_collections",
    "nakama_list_storage",
    "nakama_list_user_storage",
    "nakama_list_storage_keys",
    "nakama_get_storage_object",
    "nakama_get_storage_objects",
]
