from typing import Optional

from ..nakama_client import NakamaConsoleClient
from ..models import ListAccountsArgs, GetAccountArgs


async def nakama_list_accounts(client: NakamaConsoleClient, filter: Optional[str] = None, tombstones: Optional[bool] = None, cursor: Optional[str] = None):
    """List accounts (wrapper around GET /v2/console/account).

    Parameters mirror the Nakama Console API.
    """
    params = {}
    if filter is not None:
        params["filter"] = filter
    if tombstones is not None:
        params["tombstones"] = str(tombstones).lower()
    if cursor is not None:
        params["cursor"] = cursor
    return await client.get("/v2/console/account", params=params)


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
