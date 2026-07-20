# Nakama Console MCP (read-only)

Read-only [MCP](https://modelcontextprotocol.io/) server for Nakama Console. It logs in with console credentials, keeps the session token internally, and exposes a fixed set of query tools. No writes, no deletes.

Requires Python 3.10+ and a Nakama instance with Console reachable (dev default: `http://127.0.0.1:7351`).

## Setup

Copy `.env.example` to `.env` and fill in credentials.

| Variable | Required | Description |
| --- | --- | --- |
| `NAKAMA_NAKAMA_CONSOLE_URL` | yes | Console base URL |
| `NAKAMA_NAKAMA_USERNAME` | yes | Console admin username |
| `NAKAMA_NAKAMA_PASSWORD` | yes | Console admin password |

Yes, the env vars really do start with `NAKAMA_NAKAMA_`. Pydantic uses `env_prefix="NAKAMA_"` on fields named `nakama_*`.

```bash
pip install -r requirements.txt
python server.py --test    # optional: list a few accounts
python server.py --mcp
```

Use `--env-file path/to/.env` when the MCP client should load credentials from a non-default file.

## Tools

13 read-only tools, all marked `readOnlyHint` for MCP clients.

| Tool | What it does |
| --- | --- |
| `nakama_status` | Console URL you're connected to + node health |
| `nakama_list_accounts` | List or filter accounts by username or user id |
| `nakama_get_account` | One account: profile, devices, wallet, metadata |
| `nakama_export_account` | Full dump; `response_mode=auto\|resource\|inline` (large → MCP resource link) |
| `nakama_get_friends` | Friend list for a user |
| `nakama_get_user_groups` | Groups a user belongs to |
| `nakama_list_wallet_ledger` | Wallet ledger history; optional `after`/`before` time filters |
| `nakama_list_collections` | Storage collection names |
| `nakama_list_storage` | Storage metadata; filter by collection, key prefix, or user_id |
| `nakama_list_user_storage` | Storage metadata for one user |
| `nakama_list_storage_keys` | Keys only, no values |
| `nakama_get_storage_object` | One object; `include_value`, `max_value_chars` for truncation |
| `nakama_get_storage_objects` | Batch fetch up to **50** objects per call (no auto-chunking) |

List endpoints aggregate up to `max_objects` (default 100, cap 1000) unless you pass `cursor` for a single page. Responses include `fetched`, `complete`, `next_cursor` (when more pages exist), and `hint`.

### Agent investigation workflow

1. **`nakama_status`** — confirm which Console environment is connected.
2. **`nakama_list_user_storage`** or **`nakama_list_storage_keys`** — narrow by `user_id` / `collection`; read `hint`.
3. **`nakama_get_storage_objects`** — fetch values for known keys (≤50 per call; parallel calls OK).
4. **`nakama_list_wallet_ledger`** — currency changeset history (use `after`/`before` to narrow); `nakama_get_account` for current balances.
5. **`nakama_export_account`** — full single-user dump when needed; use `response_mode=resource` for large payloads.

See [docs/research/nakama-mcp-agent-ux.md](docs/research/nakama-mcp-agent-ux.md) for API limits and design rationale.

### Optional parameters

| Parameter | Tools | Purpose |
| --- | --- | --- |
| `cursor` | list accounts / storage / wallet ledger | Fetch one Nakama page; use `next_cursor` from prior response |
| `after` / `before` | wallet ledger | ISO-8601 time window for ledger entries |
| `include_value` | get storage object(s) | `false` = metadata only |
| `max_value_chars` | get storage object(s) | Truncate large JSON to `value_preview` |
| `response_mode` | export account | `auto` (default), `resource`, or `inline` |

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
        "${workspaceFolder}/.env"
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

## Not done yet

Leaderboard and match tools as first-class endpoints. Integration tests against a running Nakama.
