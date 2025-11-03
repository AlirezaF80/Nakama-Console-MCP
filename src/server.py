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
from .tools import register_all_tools

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def run_mcp_server(settings: Any):
    """Start the MCP stdio server using the installed `mcp` SDK.

    This function wires our Nakama client into the MCP Server by registering
    tool metadata and a tool-call dispatcher, then runs the server over stdio.
    """
    try:
        import mcp
        from mcp.server.lowlevel.server import Server
        from mcp import stdio_server
    except Exception:
        logger.exception("mcp SDK not available. Install the 'mcp' package to run as MCP server.")
        return

    client = NakamaConsoleClient(settings)
    await client.authenticate()

    # Instantiate server with a name and optional version/instructions
    server = Server(name="nakama-console-mcp", version=None, instructions="Nakama Console read-only MCP server")

    # Register all tools (account and storage)
    register_all_tools(server, client)

    logger.info("Starting MCP server 'nakama-console-mcp' over stdio...")

    # Use the stdio transport provided by the SDK
    async with stdio_server() as (read_stream, write_stream):
        initialization_options = server.create_initialization_options()
        # server.run expects (read_stream, write_stream, initialization_options)
        await server.run(read_stream, write_stream, initialization_options)

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
