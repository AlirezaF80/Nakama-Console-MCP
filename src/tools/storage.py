from typing import Optional

from ..nakama_client import NakamaConsoleClient


async def nakama_list_collections(client: NakamaConsoleClient):
    """List all storage collection names.

    Since the Nakama Console API doesn't provide a dedicated collections endpoint,
    this function discovers collections by scanning storage objects and extracting
    unique collection names. It handles pagination to find all collections.

    Returns a dict with:
        - collections: Sorted list of unique collection names
        - total_scanned: Number of storage objects scanned
        - note: Explanation of how collections were discovered
    """
    collections = set()
    cursor = None
    total_scanned = 0
    
    # Scan storage objects to extract unique collection names
    while True:
        response = await nakama_list_storage(client, cursor=cursor)
        
        objects = response.get("objects", [])
        if not objects:
            break
            
        for obj in objects:
            collection_name = obj.get("collection")
            if collection_name:
                collections.add(collection_name)
        
        total_scanned += len(objects)
        
        # Check if there are more results
        cursor = response.get("next_cursor")
        if not cursor:
            break
    
    return {
        "collections": sorted(list(collections)),
        "total_scanned": total_scanned,
        "note": "Collections discovered by scanning storage objects"
    }


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
