"""Tools package for Nakama Console MCP server."""

from typing import Any, Dict

from mcp.types import ToolAnnotations
from pydantic import ValidationError

from src.config import NakamaSettings
from src.nakama_client import NakamaConsoleClient
from src.resources import ExportCache
from src.tool_result import ToolResult, tool_result_to_json
from src.tools.registry import TOOL_SPECS, TOOL_MAP, ToolContext

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


def _normalize_result(result: ToolResult | dict[str, Any]) -> Any:
    if isinstance(result, ToolResult):
        return result.to_mcp()
    return result


def register_all_tools(
    server,
    client: NakamaConsoleClient,
    settings: NakamaSettings,
    export_cache: ExportCache,
):
    """Register all tools with the provided MCP server."""
    import mcp

    ctx = ToolContext(client=client, settings=settings, export_cache=export_cache)

    tools = [
        mcp.Tool(
            name=spec.name,
            title=spec.title,
            description=spec.description,
            inputSchema=spec.input_schema(),
            outputSchema=spec.output_schema(),
            annotations=_READONLY_ANNOTATIONS,
        )
        for spec in TOOL_SPECS
    ]

    @server.list_tools()
    async def _list_all_tools() -> list[mcp.Tool]:
        return tools

    @server.call_tool()
    async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
        spec = TOOL_MAP.get(tool_name)
        if spec is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        if spec.args_model is not None:
            try:
                validated = spec.args_model.model_validate(arguments or {})
            except ValidationError as e:
                raise ValueError(_format_validation_error(e)) from e
            kwargs = validated.model_dump(exclude_none=True)
        else:
            kwargs = {}

        result = await spec.handler(ctx, **kwargs)
        return _normalize_result(result)


__all__ = ["register_all_tools", "tool_result_to_json"]
