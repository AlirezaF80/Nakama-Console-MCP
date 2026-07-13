# Nakama Console MCP (read-only)

Read-only [MCP](https://modelcontextprotocol.io/) server for Nakama Console. It logs in with console credentials, keeps the session token internally, and exposes a fixed set of query tools. No writes, no deletes.

Requires Python 3.10+ and a Nakama instance with Console reachable (dev default: `http://127.0.0.1:7351`).

## Setup

Copy `.env.example` to `.env` and fill in credentials. For Cursor workspace configs, `.env.nakama` works too.

| Variable | Required | Description |
| --- | --- | --- |
| `NAKAMA_NAKAMA_CONSOLE_URL` | yes | Console base URL |
| `NAKAMA_NAKAMA_USERNAME` | yes | Console admin username |
| `NAKAMA_NAKAMA_PASSWORD` | yes | Console admin password |
| `NAKAMA_NAKAMA_HTTP_KEY` | no | Server HTTP key (default: `defaultkey`) |

Yes, the env vars really do start with `NAKAMA_NAKAMA_`. Pydantic uses `env_prefix="NAKAMA_"` on fields named `nakama_*`.

```bash
pip install -r requirements.txt
python server.py --test    # optional: list a few accounts
python server.py --mcp
```

Use `--env-file path/to/.env` when the MCP client should load credentials from a non-default file.

## Tools

12 read-only tools, all marked `readOnlyHint` for MCP clients.

| Tool | What it does |
| --- | --- |
| `nakama_status` | Console URL you're connected to + node health |
| `nakama_list_accounts` | List or filter accounts by username or user id |
| `nakama_get_account` | One account: profile, devices, wallet, metadata |
| `nakama_export_account` | Full dump (storage, friends, groups, messages, leaderboards, ...) |
| `nakama_get_friends` | Friend list for a user |
| `nakama_get_user_groups` | Groups a user belongs to |
| `nakama_list_collections` | Storage collection names |
| `nakama_list_storage` | Storage metadata; filter by collection, key prefix, or user_id |
| `nakama_list_user_storage` | Storage metadata for one user |
| `nakama_list_storage_keys` | Keys only, no values |
| `nakama_get_storage_object` | One object by collection / key / user_id |
| `nakama_get_storage_objects` | Batch fetch; chunks internally |

List endpoints paginate server-side up to `max_objects` (default 100, cap 1000). Truncated responses include `fetched`, `complete`, and a `hint` telling you how to narrow the query.

## MCP client config

Point at `server.py` in the repo root with `--mcp`.

### Cursor — `.cursor/mcp.json`

`mcpServers` key, `"type": "stdio"`. `--env-file` with `${workspaceFolder}` is more reliable than `envFile` alone:

```json
{
  "mcpServers": {
    "nakama-console-mcp": {
      "type": "stdio",
      "command": "python",
      "args": [
        "${workspaceFolder}/server.py",
        "--mcp",
        "--env-file",
        "${workspaceFolder}/.env.nakama"
      ],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### VS Code — `.vscode/mcp.json`

Same shape, but the top-level key is `servers`:

```json
{
  "servers": {
    "nakama-console-mcp": {
      "type": "stdio",
      "command": "python",
      "args": [
        "${workspaceFolder}/server.py",
        "--mcp",
        "--env-file",
        "${workspaceFolder}/.env"
      ],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Global config

If the server lives outside any workspace, use absolute paths and wrap under `mcpServers` (Cursor) or `servers` (VS Code):

```json
{
  "mcpServers": {
    "nakama-console-mcp": {
      "type": "stdio",
      "command": "python",
      "args": [
        "C:\\path\\to\\nakama-console-mcp\\server.py",
        "--mcp"
      ],
      "cwd": "C:\\path\\to\\nakama-console-mcp"
    }
  }
}
```

For secrets, `inputs` with `promptString` beats checking credentials into git. Env files belong in `.gitignore`.

## Tests

```bash
pytest
```

Covers validation, pagination chunking, response hints, and storage key listing. Nothing hits a live Nakama yet.

## Not done yet

Leaderboard and match tools as first-class endpoints. Integration tests against a running Nakama.
