"""Tools package for Nakama Console MCP server."""

import json
from typing import Any, Dict, Type

from mcp.types import CallToolResult, ToolAnnotations
from pydantic import BaseModel, ValidationError

from src.config import NakamaSettings
from src.nakama_client import NakamaConsoleClient
from src.models import (
    AccountEnvelope,
    CollectionsEnvelope,
    ExportAccountArgs,
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
    MAX_BATCH_OBJECTS,
    MAX_OBJECTS_HARD_LIMIT,
)
from src.resources import ExportCache
from src.response_format import DEFAULT_VALUE_PREVIEW_CHARS, MAX_VALUE_PREVIEW_CHARS

_TOOL_ARG_MODELS: Dict[str, Type[BaseModel]] = {
    "nakama_status": StatusArgs,
    "nakama_list_accounts": ListAccountsArgs,
    "nakama_get_account": GetAccountArgs,
    "nakama_export_account": ExportAccountArgs,
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


def _cursor_schema() -> Dict[str, Any]:
    return {
        "type": "string",
        "description": "Opaque cursor from a prior response next_cursor field (single page)",
    }


def _value_format_properties() -> Dict[str, Any]:
    return {
        "include_value": {
            "type": "boolean",
            "description": "Include storage value in the response (default true)",
            "default": True,
        },
        "max_value_chars": {
            "type": "integer",
            "description": (
                f"Max JSON chars before value is truncated to value_preview "
                f"(default {DEFAULT_VALUE_PREVIEW_CHARS}, max {MAX_VALUE_PREVIEW_CHARS})"
            ),
            "default": DEFAULT_VALUE_PREVIEW_CHARS,
            "minimum": 0,
            "maximum": MAX_VALUE_PREVIEW_CHARS,
        },
    }


def register_all_tools(
    server,
    client: NakamaConsoleClient,
    settings: NakamaSettings,
    export_cache: ExportCache,
):
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
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            outputSchema=_output_schema(StatusEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_accounts",
            title="List Nakama accounts",
            description=(
                "List/filter accounts. Pass cursor for one page; omit cursor to aggregate "
                f"up to max_objects (default {DEFAULT_MAX_OBJECTS}). "
                "Response includes next_cursor when more pages exist."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "User ID or username filter"},
                    "tombstones": {
                        "type": "boolean",
                        "description": "Search only recorded deletes",
                    },
                    "cursor": _cursor_schema(),
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
                "Get one account by id. Prefer over nakama_export_account unless a full dump is required."
            ),
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Nakama user id (UUID)"}},
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
                "Full account export. Very large — use response_mode=resource or auto "
                "(default) to return an MCP resource_link instead of inline JSON. "
                "Prefer targeted storage tools when you know specific keys."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Nakama user id (UUID)"},
                    "response_mode": {
                        "type": "string",
                        "enum": ["inline", "resource", "auto"],
                        "default": "auto",
                        "description": (
                            "inline: full JSON in tool result; resource: MCP resource_link; "
                            "auto: resource when export exceeds inline byte threshold"
                        ),
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
            description="Friend list for a user id.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Nakama user id (UUID)"}},
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
            description="Groups a user belongs to.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "Nakama user id (UUID)"}},
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
            description="List storage collection names.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            outputSchema=_output_schema(CollectionsEnvelope),
            annotations=_READONLY_ANNOTATIONS,
        )
    )

    tools.append(
        mcp.Tool(
            name="nakama_list_storage",
            title="List Nakama storage objects",
            description=(
                "List storage metadata (no values). Pass cursor for one page. "
                "Do not use key '%' alone. user_id-only filter has no Nakama pagination."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Filter by collection name"},
                    "key": {
                        "type": "string",
                        "description": "Suffix % prefix only (e.g. 'level%'). Requires collection.",
                    },
                    "user_id": {"type": "string", "description": "Filter by user/owner ID"},
                    "cursor": _cursor_schema(),
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
                "List storage metadata for a required user_id. Prefer when investigating one account. "
                "Many objects: consider nakama_export_account with response_mode=resource."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Nakama user id (UUID) — required"},
                    "collection": {"type": "string", "description": "Filter by collection name"},
                    "key_prefix": {
                        "type": "string",
                        "description": "Key prefix filter (appends % if omitted)",
                    },
                    "cursor": _cursor_schema(),
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
                "List keys only for a required collection. Lighter than nakama_list_storage. "
                f"When fetched > {MAX_BATCH_OBJECTS}, hint explains multiple batch-get calls."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name — required"},
                    "user_id": {"type": "string", "description": "Filter by user/owner ID"},
                    "key_prefix": {
                        "type": "string",
                        "description": "Key prefix filter (appends % if omitted)",
                    },
                    "cursor": _cursor_schema(),
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
                "Fetch one storage object. Set include_value=false for metadata only. "
                "Large values truncate to value_preview."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "key": {"type": "string", "description": "Storage object key"},
                    "user_id": {"type": "string", "description": "User/owner ID"},
                    **_value_format_properties(),
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
                f"Batch-fetch up to {MAX_BATCH_OBJECTS} objects. "
                "Make multiple calls for more keys (no auto-chunking). "
                "Use include_value=false or max_value_chars to limit payload size."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "objects": {
                        "type": "array",
                        "description": f"Storage object ids to fetch (1–{MAX_BATCH_OBJECTS})",
                        "minItems": 1,
                        "maxItems": MAX_BATCH_OBJECTS,
                        "items": {
                            "type": "object",
                            "properties": {
                                "collection": {"type": "string"},
                                "key": {"type": "string"},
                                "user_id": {"type": "string"},
                            },
                            "required": ["collection", "key", "user_id"],
                        },
                    },
                    **_value_format_properties(),
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
            return await _accounts.nakama_export_account(
                client, export_cache=export_cache, **kwargs
            )
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


def tool_result_to_json(result: Any) -> str:
    """Serialize tool results for tests."""
    if isinstance(result, CallToolResult):
        return result.content[0].text if result.content else ""
    return json.dumps(result)


__all__ = ["register_all_tools", "tool_result_to_json"]
