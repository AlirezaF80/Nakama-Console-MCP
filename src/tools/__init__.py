"""Tools package for Nakama Console MCP server."""

from typing import Any, Awaitable, Callable, Dict

from ..nakama_client import NakamaConsoleClient


def register_account_tools(server, client: NakamaConsoleClient):
    """Register account-related tools with the provided MCP `server`.

    This uses the mcp Server.list_tools and Server.call_tool decorators to
    advertise tool metadata and provide a single dispatcher for tool calls.
    """
    # lazy import to avoid circular issues
    from . import accounts as _accounts
    import mcp

    # Build tool definitions using mcp.Tool
    tools = []

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

    # register list_tools handler to populate server._tool_cache
    @server.list_tools()
    async def _list_tools() -> list[mcp.Tool]:
        return tools

    # Tool call dispatcher
    @server.call_tool()
    async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
        try:
            # dispatch based on tool_name
            if tool_name == "nakama_list_accounts":
                return await _accounts.nakama_list_accounts(client, **arguments)
            if tool_name == "nakama_get_account":
                return await _accounts.nakama_get_account(client, **arguments)
            if tool_name == "nakama_export_account":
                return await _accounts.nakama_export_account(client, **arguments)
            if tool_name == "nakama_get_wallet_ledger":
                # account_id parameter name in our client function is account_id
                return await _accounts.nakama_get_wallet_ledger(client, **arguments)
            if tool_name == "nakama_get_friends":
                return await _accounts.nakama_get_friends(client, **arguments)
            if tool_name == "nakama_get_user_groups":
                return await _accounts.nakama_get_user_groups(client, **arguments)

            return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}


__all__ = ["register_account_tools"]
