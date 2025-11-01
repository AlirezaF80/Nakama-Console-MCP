# Nakama Console MCP (read-only)

This project implements a read-only Model Context Protocol (MCP) server that exposes selected Nakama Console API endpoints as MCP tools.

Goals
- Provide safe, read-only access to Nakama Console data for AI assistants and tooling.
- Authenticate to Nakama Console using console credentials and maintain a session token internally.

Quick start
1. Copy `.env.example` to `.env` and fill in your Nakama console credentials.
2. Create a virtual environment and install dependencies:

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Run the MCP server (example):

```pwsh
python -m src.server
```

Note: The MCP server expects the `mcp` Python SDK to be available. Adjust `server.py` if your MCP SDK exposes different APIs.

Files of interest
- `src/config.py` - Pydantic settings
- `src/nakama_client.py` - Nakama Console HTTP client with authentication
- `src/server.py` - MCP server bootstrap and tool registration
- `src/tools/accounts.py` - Account-related read-only tools

Security
- This project is read-only and will not perform any write/delete operations on the Nakama server.
- Keep `.env` out of source control.

Next steps
- Implement full tool set for storage, leaderboards, matches, and server status.
- Add unit tests and integration tests against a local Nakama instance.
