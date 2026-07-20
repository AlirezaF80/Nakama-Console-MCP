import json
from typing import Any, Dict, Literal, Optional

from mcp.types import ResourceLink, TextContent

from src.envelopes import dump_envelope
from src.hints import append_hint, build_list_hint
from src.models import ListAccountsEnvelope, ListWalletLedgerEnvelope
from src.nakama_client import NakamaConsoleClient
from src.pagination import (
    DEFAULT_MAX_OBJECTS,
    clamp_max_objects,
    fetch_page_once,
    fetch_pages,
)
from src.resources import ExportCache
from src.response_format import (
    EXPORT_INLINE_MAX_BYTES,
    build_export_summary,
    export_json_size,
)
from src.tool_result import ToolResult

# Nakama Console GetWalletLedger requires limit in [1, 100]
_WALLET_LEDGER_PAGE_MAX = 100


async def nakama_list_accounts(
    client: NakamaConsoleClient,
    filter: Optional[str] = None,
    tombstones: Optional[bool] = None,
    cursor: Optional[str] = None,
    max_objects: int = DEFAULT_MAX_OBJECTS,
):
    """List accounts; auto-paginates up to max_objects unless cursor is provided."""

    async def fetch_page(page_cursor: Optional[str]):
        params = {}
        if filter is not None:
            params["filter"] = filter
        if tombstones is not None:
            params["tombstones"] = str(tombstones).lower()
        if page_cursor is not None:
            params["cursor"] = page_cursor
        return await client.get("/v2/console/account", params=params)

    if cursor is not None:
        envelope = await fetch_page_once(fetch_page, items_key="users", cursor=cursor)
    else:
        envelope = await fetch_pages(
            fetch_page, items_key="users", max_objects=max_objects
        )

    envelope["hint"] = build_list_hint(
        complete=envelope.get("complete", True),
        fetched=envelope.get("fetched", 0),
        total_count=envelope.get("total_count", 0),
        filters={"filter": filter},
        list_kind="accounts",
        next_cursor=envelope.get("next_cursor"),
    )
    return dump_envelope(ListAccountsEnvelope, envelope)


async def nakama_get_account(client: NakamaConsoleClient, id: str):
    """Get a single account by ID."""
    return await client.get(f"/v2/console/account/{id}")


async def nakama_list_wallet_ledger(
    client: NakamaConsoleClient,
    id: str,
    cursor: Optional[str] = None,
    max_objects: int = DEFAULT_MAX_OBJECTS,
    after: Optional[str] = None,
    before: Optional[str] = None,
):
    """List wallet ledger entries; auto-paginates unless cursor is provided."""
    page_limit = min(_WALLET_LEDGER_PAGE_MAX, clamp_max_objects(max_objects))

    async def fetch_page(page_cursor: Optional[str]):
        params: Dict[str, Any] = {"limit": page_limit}
        if page_cursor is not None:
            params["cursor"] = page_cursor
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        return await client.get(f"/v2/console/account/{id}/wallet", params=params)

    if cursor is not None:
        envelope = await fetch_page_once(fetch_page, items_key="items", cursor=cursor)
    else:
        envelope = await fetch_pages(
            fetch_page, items_key="items", max_objects=max_objects
        )

    hint = None
    if envelope.get("complete") and envelope.get("fetched"):
        hint = (
            "Use nakama_get_account for current wallet balances. "
            "Prefer nakama_export_account only when a full account dump is required."
        )
    if envelope.get("next_cursor"):
        hint = append_hint(hint, "Pass next_cursor to fetch the next page.")
    envelope["hint"] = hint
    return dump_envelope(ListWalletLedgerEnvelope, envelope)


async def nakama_export_account(
    client: NakamaConsoleClient,
    id: str,
    response_mode: Literal["inline", "resource", "auto"] = "auto",
    export_cache: Optional[ExportCache] = None,
) -> ToolResult:
    """Export account data inline or as an MCP resource when large."""
    data = await client.get(f"/v2/console/account/{id}/export")
    if not isinstance(data, dict):
        data = {}

    use_resource = response_mode == "resource"
    if response_mode == "auto":
        use_resource = export_json_size(data) > EXPORT_INLINE_MAX_BYTES

    if use_resource:
        if export_cache is None:
            raise RuntimeError("Export cache is not configured")
        resource_uri = export_cache.store(id, data)
        summary = build_export_summary(data)
        payload = {
            "response_mode": "resource",
            "resource_uri": resource_uri,
            "summary": summary,
            "hint": "Read the full export via the MCP resource URI.",
        }
        return ToolResult(
            structured=payload,
            content=[
                TextContent(type="text", text=json.dumps(payload, indent=2)),
                ResourceLink(
                    type="resource_link",
                    uri=resource_uri,
                    name=f"Nakama export {id}",
                    mimeType="application/json",
                ),
            ],
        )

    data["response_mode"] = "inline"
    return ToolResult(structured=data)


async def nakama_get_friends(client: NakamaConsoleClient, id: str):
    return await client.get(f"/v2/console/account/{id}/friend")


async def nakama_get_user_groups(client: NakamaConsoleClient, id: str):
    return await client.get(f"/v2/console/account/{id}/group")


__all__ = [
    "nakama_list_accounts",
    "nakama_get_account",
    "nakama_list_wallet_ledger",
    "nakama_export_account",
    "nakama_get_friends",
    "nakama_get_user_groups",
]
