"""Tools package for Nakama Console MCP server."""

from typing import Any, Awaitable, Callable, Dict

from ..nakama_client import NakamaConsoleClient


def register_all_tools(server, client: NakamaConsoleClient):
    """Register all tools (account and storage) with the provided MCP `server`.

    This uses the mcp Server.list_tools and Server.call_tool decorators to
    advertise tool metadata and provide a single dispatcher for tool calls.
    
    Note: We register all tools in one place because multiple @server.list_tools()
    decorators would overwrite each other rather than merging.
    """
    # lazy import to avoid circular issues
    from . import accounts as _accounts
    from . import storage as _storage
    import mcp

    # Build tool definitions using mcp.Tool
    tools = []

    # ==================== ACCOUNT TOOLS ====================
    
    # nakama_list_accounts
    tools.append(
        mcp.Tool(
            name="nakama_list_accounts",
            title="List Nakama accounts",
            description="List or filter Nakama accounts",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string"},
                    "tombstones": {"type": "boolean"},
                    "cursor": {"type": "string"},
                },
            },
            outputSchema=None,
        )
    )

    # nakama_get_account
    tools.append(
        mcp.Tool(
            name="nakama_get_account",
            title="Get Nakama account",
            description="Get detailed account information by id",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            },
            outputSchema=None,
        )
    )

    # nakama_export_account
    tools.append(
        mcp.Tool(
            name="nakama_export_account",
            title="Export Nakama account",
            description="Export all data for an account",
            inputSchema={"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
            outputSchema=None,
        )
    )

    # nakama_get_wallet_ledger
    tools.append(
        mcp.Tool(
            name="nakama_get_wallet_ledger",
            title="Get wallet ledger",
            description="Get wallet ledger for an account",
            inputSchema={
                "type": "object",
                "properties": {"account_id": {"type": "string"}, "limit": {"type": "integer"}, "cursor": {"type": "string"}},
                "required": ["account_id"],
            },
            outputSchema=None,
        )
    )

    # nakama_get_friends
    tools.append(
        mcp.Tool(
            name="nakama_get_friends",
            title="Get friends",
            description="Get a user's friend list",
            inputSchema={"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
            outputSchema=None,
        )
    )

    # nakama_get_user_groups
    tools.append(
        mcp.Tool(
            name="nakama_get_user_groups",
            title="Get user groups",
            description="Get groups a user belongs to",
            inputSchema={"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
            outputSchema=None,
        )
    )

    # ==================== STORAGE TOOLS ====================
    
    # nakama_list_collections
    tools.append(
        mcp.Tool(
            name="nakama_list_collections",
            title="List Nakama storage collections",
            description="List all storage collection names in Nakama",
            inputSchema={
                "type": "object",
                "properties": {},
            },
            outputSchema=None,
        )
    )

    # nakama_list_storage
    tools.append(
        mcp.Tool(
            name="nakama_list_storage",
            title="List Nakama storage objects",
            description="List storage objects with optional filters (collection, key with % prefix search, user_id) and pagination cursor",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Filter by collection name"},
                    "key": {"type": "string", "description": "Filter by key (supports % suffix for prefix search, e.g., 'level%')"},
                    "user_id": {"type": "string", "description": "Filter by user/owner ID"},
                    "cursor": {"type": "string", "description": "Pagination cursor from previous response"},
                },
            },
            outputSchema=None,
        )
    )

    # nakama_get_storage_object
    tools.append(
        mcp.Tool(
            name="nakama_get_storage_object",
            title="Get Nakama storage object",
            description="Get a specific storage object by collection, key, and user_id (returns full content including JSON value)",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "key": {"type": "string", "description": "Storage object key"},
                    "user_id": {"type": "string", "description": "User/owner ID"},
                },
                "required": ["collection", "key", "user_id"],
            },
            outputSchema=None,
        )
    )

    # ==================== REGISTRATION ====================
    
    # register list_tools handler to populate server._tool_cache
    @server.list_tools()
    async def _list_all_tools() -> list[mcp.Tool]:
        return tools

    # Tool call dispatcher for all tools
    @server.call_tool()
    async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
        try:
            # Account tools
            if tool_name == "nakama_list_accounts":
                return await _accounts.nakama_list_accounts(client, **arguments)
            if tool_name == "nakama_get_account":
                return await _accounts.nakama_get_account(client, **arguments)
            if tool_name == "nakama_export_account":
                return await _accounts.nakama_export_account(client, **arguments)
            if tool_name == "nakama_get_wallet_ledger":
                return await _accounts.nakama_get_wallet_ledger(client, **arguments)
            if tool_name == "nakama_get_friends":
                return await _accounts.nakama_get_friends(client, **arguments)
            if tool_name == "nakama_get_user_groups":
                return await _accounts.nakama_get_user_groups(client, **arguments)
            
            # Storage tools
            if tool_name == "nakama_list_collections":
                return await _storage.nakama_list_collections(client)
            if tool_name == "nakama_list_storage":
                return await _storage.nakama_list_storage(client, **arguments)
            if tool_name == "nakama_get_storage_object":
                return await _storage.nakama_get_storage_object(client, **arguments)

            return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}


# Keep old function names for backward compatibility (they just call the new one)
def register_account_tools(server, client: NakamaConsoleClient):
    """Deprecated: Use register_all_tools() instead."""
    pass  # No-op, tools are registered by register_all_tools()


def register_storage_tools(server, client: NakamaConsoleClient):
    """Deprecated: Use register_all_tools() instead."""
    pass  # No-op, tools are registered by register_all_tools()


__all__ = ["register_all_tools", "register_account_tools", "register_storage_tools"]
