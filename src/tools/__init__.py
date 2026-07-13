"""Tools package for Nakama Console MCP server."""

from typing import Any, Dict, Type

from mcp.types import ToolAnnotations
from pydantic import BaseModel, ValidationError

from src.config import NakamaSettings
from src.nakama_client import NakamaConsoleClient
from src.models import (
    AccountEnvelope,
    CollectionsEnvelope,
    ExportAccountEnvelope,
    FriendsEnvelope,
    GetAccountArgs,
    GetStorageObjectArgs,
    GetStorageObjectsArgs,
    GetStorageObjectsEnvelope,
    ListAccountsArgs,
    ListAccountsEnvelope,
    ListStorageArgs,
    ListStorageCollectionsArgs,
    ListStorageKeysArgs,
    ListStorageKeysEnvelope,
    ListStorageEnvelope,
    ListUserStorageArgs,
    StatusArgs,
    StatusEnvelope,
    StorageObjectEnvelope,
    UserGroupsEnvelope,
)
from src.pagination import (
    DEFAULT_MAX_OBJECTS,
    MAX_BATCH_INPUT,
    MAX_BATCH_OBJECTS,
    MAX_OBJECTS_HARD_LIMIT,
)

# tool_name -> Pydantic args model (GetAccountArgs reused for all id-only tools)
_TOOL_ARG_MODELS: Dict[str, Type[BaseModel]] = {
    "nakama_status": StatusArgs,
    "nakama_list_accounts": ListAccountsArgs,
    "nakama_get_account": GetAccountArgs,
    "nakama_export_account": GetAccountArgs,
    "nakama_get_friends": GetAccountArgs,
    "nakama_get_user_groups": GetAccountArgs,
    "nakama_list_collections": ListStorageCollectionsArgs,
    "nakama_list_storage": ListStorageArgs,
    "nakama_list_user_storage": ListUserStorageArgs,
    "nakama_list_storage_keys": ListStorageKeysArgs,
    "nakama_get_storage_object": GetStorageObjectArgs,
    "nakama_get_storage_objects": GetStorageObjectsArgs,
}

_READONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", ()) if x != "body")
        msg = err.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) if parts else str(exc)


def _output_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """JSON Schema for MCP Tool.outputSchema from a Pydantic envelope model."""
    return model.model_json_schema()


def _max_objects_schema() -> Dict[str, Any]:
    return {
        "type": "integer",
        "description": (
            f"Max objects to return (default {DEFAULT_MAX_OBJECTS}, "
            f"hard max {MAX_OBJECTS_HARD_LIMIT})"
        ),
        "default": DEFAULT_MAX_OBJECTS,
        "minimum": 1,
        "maximum": MAX_OBJECTS_HARD_LIMIT,
    }


def register_all_tools(server, client: NakamaConsoleClient, settings: NakamaSettings):
    """Register all tools with the provided MCP server."""
    from src.tools import accounts as _accounts
    from src.tools import status as _status
    from src.tools import storage as _storage
    import mcp

    tools = []

    tools.append(
        mcp.Tool(
            name="nakama_status",
            title="Nakama server status",
            description=(
                "Show which Nakama Console environment this MCP is connected to "
                "(console_url) and node health from GET /v2/console/status. "
                "Call first when investigating to confirm the target environment."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            outputSchema=_output_schema(StatusEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_accounts",
            title="List Nakama accounts",
            description=(
                "List/filter accounts by username or user id. Prefer nakama_get_account for one known id. "
                f"Auto-paginates up to max_objects (default {DEFAULT_MAX_OBJECTS}, "
                f"max {MAX_OBJECTS_HARD_LIMIT}); cursors stay internal. "
                "Response: users, total_count (approx), fetched, complete, hint."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "User ID or username filter",
                    },
                    "tombstones": {
                        "type": "boolean",
                        "description": "Search only recorded deletes",
                    },
                    "max_objects": _max_objects_schema(),
                },
            },
            outputSchema=_output_schema(ListAccountsEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_get_account",
            title="Get Nakama account",
            description=(
                "Get one account by id (profile, devices, wallet, metadata, disable_time). "
                "Prefer over nakama_export_account unless a full dump is required. "
                "Friends/groups: use nakama_get_friends or nakama_get_user_groups."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=_output_schema(AccountEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_export_account",
            title="Export Nakama account",
            description=(
                "Full account export: account, storage, friends, groups, messages, "
                "leaderboards, notifications, wallet ledger. "
                "Very large — prefer nakama_get_account / friends / groups / storage tools "
                "unless a full dump is required."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=_output_schema(ExportAccountEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_get_friends",
            title="Get Nakama friends",
            description=(
                "Friend list for a user id (states + related users). "
                "Not profile/wallet — use nakama_get_account for that."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=_output_schema(FriendsEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_get_user_groups",
            title="Get Nakama user groups",
            description=(
                "Groups a user belongs to (with membership state). "
                "Not account profile — use nakama_get_account for that."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Nakama user id (UUID)",
                    },
                },
                "required": ["id"],
            },
            outputSchema=_output_schema(UserGroupsEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_collections",
            title="List Nakama storage collections",
            description=(
                "List storage collection names. "
                "Explore flow: this → nakama_list_user_storage / nakama_list_storage_keys "
                "→ nakama_get_storage_objects for values."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            outputSchema=_output_schema(CollectionsEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_storage",
            title="List Nakama storage objects",
            description=(
                "List storage objects (filters: collection, key with % suffix prefix only, user_id). "
                "Metadata only — no values. Do not use key '%' alone. "
                "Response: objects, total_count, fetched, complete, hint."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Filter by collection name",
                    },
                    "key": {
                        "type": "string",
                        "description": (
                            "Filter by key (suffix % prefix only, e.g. 'level%'). "
                            "Collection is required when key is provided."
                        ),
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Filter by user/owner ID",
                    },
                    "max_objects": _max_objects_schema(),
                },
            },
            outputSchema=_output_schema(ListStorageEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_user_storage",
            title="List Nakama storage for user",
            description=(
                "List storage object metadata for a required user_id. "
                "Prefer over nakama_list_storage when investigating one account. "
                "Optional collection and key_prefix (maps to suffix % prefix filter)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Nakama user id (UUID) — required",
                    },
                    "collection": {
                        "type": "string",
                        "description": "Filter by collection name",
                    },
                    "key_prefix": {
                        "type": "string",
                        "description": "Key prefix filter (appends % if omitted)",
                    },
                    "max_objects": _max_objects_schema(),
                },
                "required": ["user_id"],
            },
            outputSchema=_output_schema(ListStorageEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_storage_keys",
            title="List Nakama storage keys",
            description=(
                "List storage keys only (no values) for a required collection. "
                "Returns [{key, user_id}, ...] plus total_count, fetched, complete, hint. "
                "Lighter than nakama_list_storage when you only need keys before batch get."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Collection name — required",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "Filter by user/owner ID",
                    },
                    "key_prefix": {
                        "type": "string",
                        "description": "Key prefix filter (appends % if omitted)",
                    },
                    "max_objects": _max_objects_schema(),
                },
                "required": ["collection"],
            },
            outputSchema=_output_schema(ListStorageKeysEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_get_storage_object",
            title="Get Nakama storage object",
            description=(
                "Fetch one storage object by collection, key, user_id; JSON-decodes value when possible. "
                "Prefer nakama_get_storage_objects for many ids after a list."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "description": "Collection name",
                    },
                    "key": {
                        "type": "string",
                        "description": "Storage object key",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User/owner ID",
                    },
                },
                "required": ["collection", "key", "user_id"],
            },
            outputSchema=_output_schema(StorageObjectEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_get_storage_objects",
            title="Get Nakama storage objects (batch)",
            description=(
                f"Batch-fetch storage objects by collection/key/user_id (1–{MAX_BATCH_INPUT}). "
                f"Auto-chunks internally in batches of {MAX_BATCH_OBJECTS}. "
                "Use after nakama_list_storage_keys or nakama_list_user_storage. "
                "Response: results, requested, chunks, fetched, failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "objects": {
                        "type": "array",
                        "description": f"Storage object ids to fetch (1–{MAX_BATCH_INPUT})",
                        "minItems": 1,
                        "maxItems": MAX_BATCH_INPUT,
                        "items": {
                            "type": "object",
                            "properties": {
                                "collection": {
                                    "type": "string",
                                    "description": "Collection name",
                                },
                                "key": {
                                    "type": "string",
                                    "description": "Storage object key",
                                },
                                "user_id": {
                                    "type": "string",
                                    "description": "User/owner ID",
                                },
                            },
                            "required": ["collection", "key", "user_id"],
                        },
                    },
                },
                "required": ["objects"],
            },
            outputSchema=_output_schema(GetStorageObjectsEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    @server.list_tools()
    async def _list_all_tools() -> list[mcp.Tool]:
        return tools

    @server.call_tool()
    async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
        model_cls = _TOOL_ARG_MODELS.get(tool_name)
        if model_cls is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            validated = model_cls.model_validate(arguments or {})
        except ValidationError as e:
            raise ValueError(_format_validation_error(e)) from e

        kwargs = validated.model_dump(exclude_none=True)

        if tool_name == "nakama_status":
            return await _status.nakama_status(client, settings)
        if tool_name == "nakama_list_accounts":
            return await _accounts.nakama_list_accounts(client, **kwargs)
        if tool_name == "nakama_get_account":
            return await _accounts.nakama_get_account(client, **kwargs)
        if tool_name == "nakama_export_account":
            return await _accounts.nakama_export_account(client, **kwargs)
        if tool_name == "nakama_get_friends":
            return await _accounts.nakama_get_friends(client, **kwargs)
        if tool_name == "nakama_get_user_groups":
            return await _accounts.nakama_get_user_groups(client, **kwargs)
        if tool_name == "nakama_list_collections":
            return await _storage.nakama_list_collections(client)
        if tool_name == "nakama_list_storage":
            return await _storage.nakama_list_storage(client, **kwargs)
        if tool_name == "nakama_list_user_storage":
            return await _storage.nakama_list_user_storage(client, **kwargs)
        if tool_name == "nakama_list_storage_keys":
            return await _storage.nakama_list_storage_keys(client, **kwargs)
        if tool_name == "nakama_get_storage_object":
            return await _storage.nakama_get_storage_object(client, **kwargs)
        if tool_name == "nakama_get_storage_objects":
            return await _storage.nakama_get_storage_objects(client, **kwargs)

        raise ValueError(f"Unknown tool: {tool_name}")


__all__ = ["register_all_tools"]
