"""Response shaping helpers for MCP tool outputs."""

import json
from typing import Any, Dict

DEFAULT_VALUE_PREVIEW_CHARS = 2000
MAX_VALUE_PREVIEW_CHARS = 10000
EXPORT_INLINE_MAX_BYTES = 100_000
EXPORT_USER_STORAGE_HINT_THRESHOLD = 20


def _value_as_text(value: Any) -> tuple[str, int]:
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return value, len(encoded)
    text = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return text, len(text.encode("utf-8"))


def format_storage_object(
    obj: Any,
    *,
    include_value: bool = True,
    max_value_chars: int = DEFAULT_VALUE_PREVIEW_CHARS,
) -> Any:
    """Shape a storage object for MCP output with optional value omission/truncation."""
    if not isinstance(obj, dict):
        return obj

    result = dict(obj)
    if not include_value:
        result.pop("value", None)
        return result

    if "value" not in result:
        return result

    text, byte_len = _value_as_text(result["value"])
    if len(text) <= max_value_chars:
        return result

    result.pop("value", None)
    result["value_preview"] = text[:max_value_chars]
    result["value_truncated"] = True
    result["value_bytes"] = byte_len
    return result


def export_json_size(data: Dict[str, Any]) -> int:
    """Approximate UTF-8 byte size of export JSON."""
    return len(
        json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def build_export_summary(data: Dict[str, Any]) -> Dict[str, int]:
    """Count major sections in a Nakama account export payload."""

    def _len(*keys: str) -> int:
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
        return 0

    return {
        "storage_objects": _len("objects", "storage"),
        "friends": _len("friends"),
        "groups": _len("groups"),
        "messages": _len("messages"),
        "notifications": _len("notifications"),
        "leaderboard_records": _len("leaderboard_records"),
        "wallet_ledger": _len("wallet_ledgers", "wallet_ledger"),
    }


__all__ = [
    "DEFAULT_VALUE_PREVIEW_CHARS",
    "MAX_VALUE_PREVIEW_CHARS",
    "EXPORT_INLINE_MAX_BYTES",
    "EXPORT_USER_STORAGE_HINT_THRESHOLD",
    "format_storage_object",
    "export_json_size",
    "build_export_summary",
]
