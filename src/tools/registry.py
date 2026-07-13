"""Declarative registry of Nakama Console MCP tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Type

from pydantic import BaseModel

from src.config import NakamaSettings
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
    ListStorageKeysArgs,
    ListStorageKeysEnvelope,
    ListStorageEnvelope,
    ListUserStorageArgs,
    StatusEnvelope,
    StorageObjectEnvelope,
    UserGroupsEnvelope,
)
from src.nakama_client import NakamaConsoleClient
from src.pagination import DEFAULT_MAX_OBJECTS, MAX_BATCH_OBJECTS
from src.resources import ExportCache
from src.tool_result import ToolResult
from src.tools import accounts, status, storage

Handler = Callable[..., Awaitable[ToolResult | dict[str, Any]]]


@dataclass(frozen=True)
class ToolContext:
    client: NakamaConsoleClient
    settings: NakamaSettings
    export_cache: ExportCache


@dataclass(frozen=True)
class ToolSpec:
    name: str
    title: str
    description: str
    args_model: Optional[Type[BaseModel]]
    output_model: Type[BaseModel]
    handler: Handler

    def input_schema(self) -> Dict[str, Any]:
        if self.args_model is None:
            return {"type": "object", "properties": {}, "additionalProperties": False}
        return self.args_model.model_json_schema()

    def output_schema(self) -> Dict[str, Any]:
        return self.output_model.model_json_schema()


async def _status(ctx: ToolContext, **_: Any) -> ToolResult:
    return ToolResult(structured=await status.nakama_status(ctx.client, ctx.settings))


async def _list_accounts(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await accounts.nakama_list_accounts(ctx.client, **kwargs)
    )


async def _get_account(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await accounts.nakama_get_account(ctx.client, **kwargs)
    )


async def _export_account(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return await accounts.nakama_export_account(
        ctx.client, export_cache=ctx.export_cache, **kwargs
    )


async def _get_friends(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await accounts.nakama_get_friends(ctx.client, **kwargs)
    )


async def _get_user_groups(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await accounts.nakama_get_user_groups(ctx.client, **kwargs)
    )


async def _list_collections(ctx: ToolContext, **_: Any) -> ToolResult:
    return ToolResult(structured=await storage.nakama_list_collections(ctx.client))


async def _list_storage(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await storage.nakama_list_storage(ctx.client, **kwargs)
    )


async def _list_user_storage(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await storage.nakama_list_user_storage(ctx.client, **kwargs)
    )


async def _list_storage_keys(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await storage.nakama_list_storage_keys(ctx.client, **kwargs)
    )


async def _get_storage_object(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await storage.nakama_get_storage_object(ctx.client, **kwargs)
    )


async def _get_storage_objects(ctx: ToolContext, **kwargs: Any) -> ToolResult:
    return ToolResult(
        structured=await storage.nakama_get_storage_objects(ctx.client, **kwargs)
    )


TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="nakama_status",
        title="Nakama server status",
        description=(
            "Show which Nakama Console environment this MCP is connected to "
            "(console_url) and node health from GET /v2/console/status. "
            "Call first when investigating to confirm the target environment."
        ),
        args_model=None,
        output_model=StatusEnvelope,
        handler=_status,
    ),
    ToolSpec(
        name="nakama_list_accounts",
        title="List Nakama accounts",
        description=(
            "List/filter accounts. Pass cursor for one page; omit cursor to aggregate "
            f"up to max_objects (default {DEFAULT_MAX_OBJECTS}). "
            "Response includes next_cursor when more pages exist."
        ),
        args_model=ListAccountsArgs,
        output_model=ListAccountsEnvelope,
        handler=_list_accounts,
    ),
    ToolSpec(
        name="nakama_get_account",
        title="Get Nakama account",
        description=(
            "Get one account by id. Prefer over nakama_export_account unless a full dump is required."
        ),
        args_model=GetAccountArgs,
        output_model=AccountEnvelope,
        handler=_get_account,
    ),
    ToolSpec(
        name="nakama_export_account",
        title="Export Nakama account",
        description=(
            "Full account export. Very large — use response_mode=resource or auto "
            "(default) to return an MCP resource_link instead of inline JSON. "
            "Prefer targeted storage tools when you know specific keys."
        ),
        args_model=ExportAccountArgs,
        output_model=ExportAccountEnvelope,
        handler=_export_account,
    ),
    ToolSpec(
        name="nakama_get_friends",
        title="Get Nakama friends",
        description="Friend list for a user id.",
        args_model=GetAccountArgs,
        output_model=FriendsEnvelope,
        handler=_get_friends,
    ),
    ToolSpec(
        name="nakama_get_user_groups",
        title="Get Nakama user groups",
        description="Groups a user belongs to.",
        args_model=GetAccountArgs,
        output_model=UserGroupsEnvelope,
        handler=_get_user_groups,
    ),
    ToolSpec(
        name="nakama_list_collections",
        title="List Nakama storage collections",
        description="List storage collection names.",
        args_model=None,
        output_model=CollectionsEnvelope,
        handler=_list_collections,
    ),
    ToolSpec(
        name="nakama_list_storage",
        title="List Nakama storage objects",
        description=(
            "List storage metadata (no values). Pass cursor for one page. "
            "Do not use key '%' alone. user_id-only filter has no Nakama pagination."
        ),
        args_model=ListStorageArgs,
        output_model=ListStorageEnvelope,
        handler=_list_storage,
    ),
    ToolSpec(
        name="nakama_list_user_storage",
        title="List Nakama storage for user",
        description=(
            "List storage metadata for a required user_id. Prefer when investigating one account. "
            "Many objects: consider nakama_export_account with response_mode=resource."
        ),
        args_model=ListUserStorageArgs,
        output_model=ListStorageEnvelope,
        handler=_list_user_storage,
    ),
    ToolSpec(
        name="nakama_list_storage_keys",
        title="List Nakama storage keys",
        description=(
            "List keys only for a required collection. Lighter than nakama_list_storage. "
            f"When fetched > {MAX_BATCH_OBJECTS}, hint explains multiple batch-get calls."
        ),
        args_model=ListStorageKeysArgs,
        output_model=ListStorageKeysEnvelope,
        handler=_list_storage_keys,
    ),
    ToolSpec(
        name="nakama_get_storage_object",
        title="Get Nakama storage object",
        description=(
            "Fetch one storage object. Set include_value=false for metadata only. "
            "Large values truncate to value_preview."
        ),
        args_model=GetStorageObjectArgs,
        output_model=StorageObjectEnvelope,
        handler=_get_storage_object,
    ),
    ToolSpec(
        name="nakama_get_storage_objects",
        title="Get Nakama storage objects (batch)",
        description=(
            f"Batch-fetch up to {MAX_BATCH_OBJECTS} objects. "
            "Make multiple calls for more keys (no auto-chunking). "
            "Use include_value=false or max_value_chars to limit payload size."
        ),
        args_model=GetStorageObjectsArgs,
        output_model=GetStorageObjectsEnvelope,
        handler=_get_storage_objects,
    ),
]

TOOL_MAP: Dict[str, ToolSpec] = {spec.name: spec for spec in TOOL_SPECS}


__all__ = ["ToolContext", "ToolSpec", "TOOL_SPECS", "TOOL_MAP"]
