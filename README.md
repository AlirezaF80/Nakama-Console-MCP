# Nakama Console MCP (read-only)

This project implements a read-only Model Context Protocol (MCP) server that exposes selected Nakama Console API endpoints as MCP tools.

## Goals

- Provide safe, read-only access to Nakama Console data for AI assistants and tooling.
- Authenticate to Nakama Console using console credentials and maintain a session token internally.

## Quick start

1. Copy `.env.example` to `.env` and fill in your Nakama console credentials.
2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run the MCP server (example):

```pwsh
python server.py --mcp
```

## Configuring the Local MCP entry (mcp.json)

If you run the MCP server from the VS Code LocalProcess MCP host (or any client that reads an `mcp.json` file), you need to point the `nakama-console-mcp` entry to the root `server.py` we provide. Below are recommended examples.

**1. User/global `mcp.json` (Windows absolute path example)**

Place or update the `nakama-console-mcp` entry in your `mcp.json` (this is typically the file stored under your VS Code user data / roaming profile) so it points to the repository `server.py` and passes the `--mcp` flag:

```json
"nakama-console-mcp": {
 "type": "stdio",
 "command": "python",
 "args": [
  "C:\\MCP Servers\\Nakama-Console-MCP\\server.py",
  "--mcp"
 ]
}
```

**2. Per-workspace `.cursor/mcp.json` (Cursor — recommended for project-specific configs)**

Cursor uses `.cursor/mcp.json` (not `.vscode/mcp.json`). STDIO servers require `"type": "stdio"`.
Pass the project env file via `--env-file` with `${workspaceFolder}` interpolation (more reliable than `envFile` alone):

```json
{
  "mcpServers": {
    "nakama-console-mcp": {
      "type": "stdio",
      "command": "python",
      "args": [
        "C:\\MCP Servers\\nakama-console-mcp\\server.py",
        "--mcp",
        "--env-file",
        "${workspaceFolder}/.env.nakama"
      ],
      "cwd": "C:\\MCP Servers\\nakama-console-mcp"
    }
  }
}
```

**VS Code** uses `.vscode/mcp.json` with a `"servers"` key instead of `"mcpServers"`.

**Alternative:** reference a workspace-local env file (if you prefer `.env` files):

```json
{
 "servers": {
  "nakama-console-mcp": {
   "type": "stdio",
   "command": "python",
   "args": ["-m", "src.server", "--mcp"],
   "cwd": "${workspaceFolder}",
   "envFile": "${workspaceFolder}/.env.nakama"
  }
 }
}
```

**Security note:** prefer using `inputs` (promptString) for secrets so VS Code stores them securely rather than checking secrets into source control. If you use an env file, keep it out of version control (add to `.gitignore`).

## List tools (auto-pagination)

`nakama_list_accounts` and `nakama_list_storage` auto-paginate Console pages up to `max_objects` (default **100**, hard max **1000**). Agents never pass or receive cursors.

Response envelope:

- `users` / `objects` — items returned this call
- `total_count` — approximate total matching the filter (from Nakama)
- `fetched` — number of items in this response
- `complete` — `true` if all matches were returned; if `false`, raise `max_objects` or narrow filters

Use `total_count` when you only need an approximate size without fetching every key.

## Security

- This project is read-only for now, and will not perform any write/delete operations on the Nakama server.
- Keep `.env` out of source control.

## Next steps

- Implement full tool set for storage, leaderboards, matches, and server status.
- Add unit tests and integration tests against a local Nakama instance.
