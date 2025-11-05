from typing import Optional
import json

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
    # Use the Console API Explorer to call the ReadStorageObjects client API
    # The console endpoint expects a JSON body as a string in the `body` field.
    read_request = {"objectIds": [{"collection": collection, "key": key}]}

    payload = {
        "user_id": user_id,
        "body": json.dumps(read_request),
        "session_vars": {},
    }

    resp = await client.post("/v2/console/api/endpoints/ReadStorageObjects", json_data=payload)

    # The console proxy returns a JSON with a `body` field that is itself a JSON string
    # containing the actual ReadStorageObjects response. Example: {"body": "{\"objects\": [...]}"}
    if not resp:
        return resp

    # If an error message was returned by the proxy, propagate it
    if isinstance(resp, dict) and resp.get("error_message"):
        return resp

    body_str = None
    if isinstance(resp, dict) and "body" in resp:
        body_str = resp.get("body")

    if not body_str:
        # Fall back to returning raw response if unexpected shape
        return resp

    try:
        body = json.loads(body_str)
    except Exception:
        # If body is not valid JSON, return the raw body string
        return {"body": body_str}

    objects = body.get("objects") if isinstance(body, dict) else None
    if not objects:
        return body

    obj = objects[0]

    # If the storage object's value is a JSON-encoded string, parse it for convenience.
    value = obj.get("value")
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            obj["value"] = parsed
        except Exception:
            # leave as string if not JSON
            pass

    return obj


__all__ = [
    "nakama_list_collections",
    "nakama_list_storage",
    "nakama_get_storage_object",
]
