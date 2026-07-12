from typing import Optional

from src.nakama_client import NakamaConsoleClient
from src.pagination import DEFAULT_MAX_OBJECTS, fetch_pages


async def nakama_list_accounts(
    client: NakamaConsoleClient,
    filter: Optional[str] = None,
    tombstones: Optional[bool] = None,
    max_objects: int = DEFAULT_MAX_OBJECTS,
):
    """List accounts; auto-paginates up to max_objects.

    Parameters mirror the Nakama Console API filters, plus max_objects.
    Returns an envelope with users, total_count (approximate), fetched, and complete.
    """

    async def fetch_page(cursor: Optional[str]):
        params = {}
        if filter is not None:
            params["filter"] = filter
        if tombstones is not None:
            params["tombstones"] = str(tombstones).lower()
        if cursor is not None:
            params["cursor"] = cursor
        return await client.get("/v2/console/account", params=params)

    return await fetch_pages(fetch_page, items_key="users", max_objects=max_objects)


async def nakama_get_account(client: NakamaConsoleClient, id: str):
    """Get a single account by ID."""
    return await client.get(f"/v2/console/account/{id}")


async def nakama_export_account(client: NakamaConsoleClient, id: str):
    return await client.get(f"/v2/console/account/{id}/export")


async def nakama_get_friends(client: NakamaConsoleClient, id: str):
    return await client.get(f"/v2/console/account/{id}/friend")


async def nakama_get_user_groups(client: NakamaConsoleClient, id: str):
    return await client.get(f"/v2/console/account/{id}/group")


__all__ = [
    "nakama_list_accounts",
    "nakama_get_account",
    "nakama_export_account",
    "nakama_get_friends",
    "nakama_get_user_groups",
]
