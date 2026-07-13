"""Input validation helpers for Nakama Console MCP tools."""

from typing import Optional


def validate_storage_key_filter(key: Optional[str]) -> Optional[str]:
    """Validate and normalize a storage key filter for list endpoints.

    Nakama Console supports exact key match or prefix search via a trailing ``%``.
    Raises ValueError with actionable messages for common agent mistakes.
    """
    if key is None:
        return None

    stripped = key.strip()
    if not stripped:
        return None

    if stripped == "%" or stripped.replace("%", "").strip() == "":
        raise ValueError(
            "Omit key; use collection (+ optional user_id) to list objects in scope"
        )

    pct_count = stripped.count("%")
    if pct_count > 1:
        raise ValueError("Only one trailing % allowed for prefix search")
    if pct_count == 1 and not stripped.endswith("%"):
        raise ValueError("Only suffix % prefix search is supported (e.g. 'level%')")

    return stripped


def key_prefix_to_filter(key_prefix: Optional[str]) -> Optional[str]:
    """Map a key_prefix argument to a Nakama key filter with trailing %."""
    if key_prefix is None:
        return None

    prefix = key_prefix.strip()
    if not prefix:
        return None

    if not prefix.endswith("%"):
        prefix = f"{prefix}%"

    return validate_storage_key_filter(prefix)


def _is_prefix_key(key: Optional[str]) -> bool:
    return bool(key and key.endswith("%") and key.count("%") == 1)


def validate_storage_list_cursor(
    *,
    collection: Optional[str],
    key: Optional[str],
    user_id: Optional[str],
    cursor: Optional[str],
) -> None:
    """Reject cursor/filter combos Nakama Console disallows."""
    if not cursor:
        return

    if user_id and not collection and not key:
        raise ValueError(
            "Cursor not allowed when filter only contains user ID. Add collection to narrow scope."
        )

    if user_id and collection and key and not _is_prefix_key(key):
        raise ValueError(
            "Cursor not allowed when filter only contains collection, key, and user_id."
        )


__all__ = [
    "validate_storage_key_filter",
    "key_prefix_to_filter",
    "validate_storage_list_cursor",
]
