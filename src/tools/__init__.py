"""Tools package for Nakama Console MCP server."""

from ..nakama_client import NakamaConsoleClient


def register_account_tools(server, client: NakamaConsoleClient):
    """Register account tools on the provided MCP server.

    The MCP SDK API surface may differ; this function tries two common
    registration methods:
      - server.register_tool(name, callable)
      - server.tool()(callable) pattern

    Adjust as needed for your MCP SDK.
    """
    # Import lazily to avoid circular imports when running tests
    from . import accounts as _accounts

    # Prefer explicit register_tool if available
    try:
        server.register_tool("nakama_list_accounts", _accounts.nakama_list_accounts, client=client)
    except Exception:
        # Fallback: attach to server.tools dict if present
        try:
            if not hasattr(server, "tools"):
                server.tools = {}
            server.tools["nakama_list_accounts"] = lambda **kwargs: _accounts.nakama_list_accounts(client=client, **kwargs)
        except Exception:
            raise


__all__ = ["register_account_tools"]
