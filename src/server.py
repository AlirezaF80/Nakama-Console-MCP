"""MCP server bootstrap for Nakama Console (read-only).

This module is intentionally small: it loads settings, creates the Nakama client,
registers tools, and runs the MCP server.

You may need to adapt the `mcp` calls depending on your MCP SDK version.
"""
import argparse
import asyncio
import logging
import sys
from typing import Any

from .config import load_settings
from .nakama_client import NakamaConsoleClient
from .tools import register_account_tools

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def run_mcp_server(settings: Any):
    """Attempt to start the official MCP server. If `mcp` package is missing,
    this function will warn and return.
    """
    try:
        from mcp import Server
    except Exception:
        logger.warning(
            "`mcp` package not available or import failed. Install the official MCP SDK to run as an MCP server."
        )
        return

    client = NakamaConsoleClient(settings)
    await client.authenticate()

    server = Server(server_name="nakama-console-mcp")
    # Register tools (best-effort; adjust for your MCP SDK if needed)
    register_account_tools(server, client)

    logger.info("Starting MCP server 'nakama-console-mcp'...")
    try:
        # The exact run API may differ depending on mcp SDK version.
        await server.run_stdio()
    except AttributeError:
        logger.warning("`Server.run_stdio()` not available on this MCP SDK. Implement the correct entrypoint for your MCP server.")
    finally:
        await client.close()


async def cli_test_list_accounts(settings: Any, limit: int = 5):
    """Simple CLI test that authenticates and lists a few accounts using the client.

    This is useful for verifying connectivity without installing the MCP SDK.
    """
    client = NakamaConsoleClient(settings)
    await client.authenticate()
    try:
        data = await client.get("/v2/console/account")
        users = data.get("users") if isinstance(data, dict) else data
        if not users:
            print("No users returned or empty response")
            return
        print(f"Showing up to {limit} users:")
        for u in users[:limit]:
            # print a few identifying fields if available
            uid = u.get("id") or u.get("user", {}).get("id") if isinstance(u, dict) else None
            username = u.get("username") or (u.get("user") or {}).get("username") if isinstance(u, dict) else None
            print(f"- id={uid} username={username}")
    finally:
        await client.close()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mcp", action="store_true", help="Run as MCP server (requires mcp SDK)")
    p.add_argument("--test", action="store_true", help="Run a CLI connectivity test (authenticate and list accounts)")
    p.add_argument("--limit", type=int, default=5, help="Number of accounts to show in --test mode")
    return p.parse_args()


def main():
    args = parse_args()
    settings = load_settings()
    if args.mcp:
        asyncio.run(run_mcp_server(settings))
        return
    if args.test:
        asyncio.run(cli_test_list_accounts(settings, limit=args.limit))
        return

    print("No mode selected. Use --test to run a connectivity test or --mcp to run as an MCP server.")


if __name__ == "__main__":
    main()
