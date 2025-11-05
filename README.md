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

**2. Per-workspace `.vscode/mcp.json` (recommended for project-specific configs)**

For project-specific configurations, add an `mcp.json` under the workspace's `.vscode/` folder. This keeps the configuration alongside the project and lets VS Code automatically start the correct MCP server for that workspace.

Example that uses secure input variables (recommended):

```json
{
 "servers": {
  "nakama-console-mcp": {
   "type": "stdio",
   "command": "python",
   "args": ["-m", "src.server", "--mcp"],
   "cwd": "${workspaceFolder}",
   "env": {
    "NAKAMA_NAKAMA_CONSOLE_URL": "${input:nakama_url}",
    "NAKAMA_NAKAMA_USERNAME": "${input:nakama_user}",
    "NAKAMA_NAKAMA_PASSWORD": "${input:nakama_pass}",
    "NAKAMA_NAKAMA_HTTP_KEY": "${input:nakama_key}"
   }
  }
 },
 "inputs": [
  { "id": "nakama_url", "type": "promptString", "description": "Nakama Console URL" },
  { "id": "nakama_user", "type": "promptString", "description": "Nakama Username" },
  { "id": "nakama_pass", "type": "promptString", "description": "Nakama Password", "password": true },
  { "id": "nakama_key", "type": "promptString", "description": "Nakama HTTP Key" }
 ]
}
```

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

## Security

- This project is read-only for now, and will not perform any write/delete operations on the Nakama server.
- Keep `.env` out of source control.

## Next steps

- Implement full tool set for storage, leaderboards, matches, and server status.
- Add unit tests and integration tests against a local Nakama instance.
