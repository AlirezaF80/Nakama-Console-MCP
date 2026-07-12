"""Tools package for Nakama Console MCP server."""

from typing import Any, Dict, Type

from mcp.types import ToolAnnotations
from pydantic import BaseModel, ValidationError

from src.nakama_client import NakamaConsoleClient
from src.models import (
    GetAccountArgs,
    GetStorageObjectArgs,
    GetStorageObjectsArgs,
    ListAccountsArgs,
    ListStorageArgs,
    ListStorageCollectionsArgs,
)

# tool_name -> Pydantic args model (GetAccountArgs reused for all id-only tools)
_TOOL_ARG_MODELS: Dict[str, Type[BaseModel]] = {
    "nakama_list_accounts": ListAccountsArgs,
    "nakama_get_account": GetAccountArgs,
    "nakama_export_account": GetAccountArgs,
    "nakama_get_friends": GetAccountArgs,
    "nakama_get_user_groups": GetAccountArgs,
    "nakama_list_collections": ListStorageCollectionsArgs,
    "nakama_list_storage": ListStorageArgs,
    "nakama_get_storage_object": GetStorageObjectArgs,
    "nakama_get_storage_objects": GetStorageObjectsArgs,
}

_READONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,  # closed Nakama Console data plane
)


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", ()) if x != "body")
        msg = err.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) if parts else str(exc)


def register_all_tools(server, client: NakamaConsoleClient):
    """Register all tools (account and storage) with the provided MCP `server`.

    This uses the mcp Server.list_tools and Server.call_tool decorators to
    advertise tool metadata and provide a single dispatcher for tool calls.
    
    Note: We register all tools in one place because multiple @server.list_tools()
    decorators would overwrite each other rather than merging.
    """
    # lazy import to avoid circular issues
    from src.tools import accounts as _accounts
    from src.tools import storage as _storage
    import mcp

    # Build tool definitions using mcp.Tool
    tools = []

    # ==================== ACCOUNT TOOLS ====================
    
    # nakama_list_accounts
    tools.append(
        mcp.Tool(
            name="nakama_list_accounts",
            title="List Nakama accounts",
            description=(
                "List/filter accounts by username or user id. Prefer nakama_get_account for one known id. "
                "Auto-paginates up to max_objects (default 100, max 1000); cursors stay internal. "
                "Response: users, total_count (approx), fetched, complete. "
                "If complete is false, raise max_objects or narrow filter."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "User ID or username filter",
                    },
                    "tombstones": {
                        "type": "boolean",
                        "description": "Search only recorded deletes",
                    },
                    "max_objects": {
                        "type": "integer",
                        "description": "Max accounts to return (default 100, hard max 1000)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000,
                    },
                },
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_get_account
    tools.append(
        mcp.Tool(
            name="nakama_get_account",
            title="Get Nakama account",
            description=(
                "Get one account by id (profile, devices, wallet, metadata, disable_time). "
                "Prefer over nakama_export_account unless a full dump is required. "
                "Friends/groups: use nakama_get_friends or nakama_get_user_groups."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_export_account
    tools.append(
        mcp.Tool(
            name="nakama_export_account",
            title="Export Nakama account",
            description=(
                "Full account export: account, storage, friends, groups, messages, "
                "leaderboards, notifications, wallet ledger. "
                "Very large — prefer nakama_get_account / friends / groups / storage tools "
                "unless a full dump is required."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_get_friends
    tools.append(
        mcp.Tool(
            name="nakama_get_friends",
            title="Get Nakama friends",
            description=(
                "Friend list for a user id (states + related users). "
                "Not profile/wallet — use nakama_get_account for that."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_get_user_groups
    tools.append(
        mcp.Tool(
            name="nakama_get_user_groups",
            title="Get Nakama user groups",
            description=(
                "Groups a user belongs to (with membership state). "
                "Not account profile — use nakama_get_account for that."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # ==================== STORAGE TOOLS ====================
    
    # nakama_list_collections
    tools.append(
        mcp.Tool(
            name="nakama_list_collections",
            title="List Nakama storage collections",
            description=(
                "List storage collection names. "
                "Explore flow: this → nakama_list_storage → nakama_get_storage_object(s) for values."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_list_storage
    tools.append(
        mcp.Tool(
            name="nakama_list_storage",
            title="List Nakama storage objects",
            description=(
                "List storage objects (filters: collection, key with % prefix, user_id). "
                "Metadata only — no values. Auto-paginates up to max_objects. "
                "Response: objects, total_count (approx), fetched, complete. "
                "If complete is false, raise max_objects (max 1000) or narrow filters. "
                "Load values via nakama_get_storage_objects (batch) or nakama_get_storage_object."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Filter by collection name",
                    },
                    "key": {
                        "type": "string",
                        "description": (
                            "Filter by key (supports % suffix for prefix search, e.g., 'level%'). "
                            "Optional, but collection is required if key is provided"
                        ),
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Filter by user/owner ID",
                    },
                    "max_objects": {
                        "type": "integer",
                        "description": "Max objects to return (default 100, hard max 1000)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000,
                    },
                },
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_get_storage_object
    tools.append(
        mcp.Tool(
            name="nakama_get_storage_object",
            title="Get Nakama storage object",
            description=(
                "Fetch one storage object by collection, key, user_id; JSON-decodes value when possible. "
                "Prefer nakama_get_storage_objects for many ids after a list."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Collection name",
                    },
                    "key": {
                        "type": "string",
                        "description": "Storage object key",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User/owner ID",
                    },
                },
                "required": ["collection", "key", "user_id"],
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # nakama_get_storage_objects
    tools.append(
        mcp.Tool(
            name="nakama_get_storage_objects",
            title="Get Nakama storage objects (batch)",
            description=(
                "Batch-fetch storage objects by collection/key/user_id (1–50). "
                "Use after nakama_list_storage to load values. "
                "Response: results (input order; ok+object or ok+error), fetched, failed. "
                "Per-item failures do not abort the batch."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "objects": {
                        "type": "array",
                        "description": "Storage object ids to fetch (1–50)",
                        "minItems": 1,
                        "maxItems": 50,
                        "items": {
                            "type": "object",
                            "properties": {
                                "collection": {
                                    "type": "string",
                                    "description": "Collection name",
                                },
                                "key": {
                                    "type": "string",
                                    "description": "Storage object key",
                                },
                                "user_id": {
                                    "type": "string",
                                    "description": "User/owner ID",
                                },
                            },
                            "required": ["collection", "key", "user_id"],
                        },
                    },
                },
                "required": ["objects"],
            },
            outputSchema=None,
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    # ==================== REGISTRATION ====================
    
    # register list_tools handler to populate server._tool_cache
    @server.list_tools()
    async def _list_all_tools() -> list[mcp.Tool]:
        return tools

    # Tool call dispatcher for all tools.
    # Exceptions propagate so the MCP SDK returns CallToolResult(isError=True).
    @server.call_tool()
    async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
        model_cls = _TOOL_ARG_MODELS.get(tool_name)
        if model_cls is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            validated = model_cls.model_validate(arguments or {})
        except ValidationError as e:
            raise ValueError(_format_validation_error(e)) from e

        kwargs = validated.model_dump(exclude_none=True)

        if tool_name == "nakama_list_accounts":
            return await _accounts.nakama_list_accounts(client, **kwargs)
        if tool_name == "nakama_get_account":
            return await _accounts.nakama_get_account(client, **kwargs)
        if tool_name == "nakama_export_account":
            return await _accounts.nakama_export_account(client, **kwargs)
        if tool_name == "nakama_get_friends":
            return await _accounts.nakama_get_friends(client, **kwargs)
        if tool_name == "nakama_get_user_groups":
            return await _accounts.nakama_get_user_groups(client, **kwargs)
        if tool_name == "nakama_list_collections":
            return await _storage.nakama_list_collections(client)
        if tool_name == "nakama_list_storage":
            return await _storage.nakama_list_storage(client, **kwargs)
        if tool_name == "nakama_get_storage_object":
            return await _storage.nakama_get_storage_object(client, **kwargs)
        if tool_name == "nakama_get_storage_objects":
            return await _storage.nakama_get_storage_objects(client, **kwargs)

        raise ValueError(f"Unknown tool: {tool_name}")


# Keep old function names for backward compatibility (they just call the new one)
def register_account_tools(server, client: NakamaConsoleClient):
    """Deprecated: Use register_all_tools() instead."""
    pass  # No-op, tools are registered by register_all_tools()


def register_storage_tools(server, client: NakamaConsoleClient):
    """Deprecated: Use register_all_tools() instead."""
    pass  # No-op, tools are registered by register_all_tools()


__all__ = ["register_all_tools", "register_account_tools", "register_storage_tools"]
