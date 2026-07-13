"""Normalized tool handler return type for MCP dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from mcp.types import ContentBlock


@dataclass
class ToolResult:
    """Structured MCP tool output with optional extra content blocks."""

    structured: Any
    content: Optional[List[ContentBlock]] = None

    def to_mcp(self) -> Any:
        if self.content is not None:
            return self.content, self.structured
        return self.structured


def tool_result_to_json(result: Any) -> str:
    """Serialize tool results for tests."""
    import json

    if isinstance(result, ToolResult):
        return json.dumps(result.structured)
    if isinstance(result, tuple) and len(result) == 2:
        _content, structured = result
        return json.dumps(structured)
    return json.dumps(result)


__all__ = ["ToolResult", "tool_result_to_json"]
