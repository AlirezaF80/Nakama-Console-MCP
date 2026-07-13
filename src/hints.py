"""Hint builders for list tool response envelopes."""

import math
from typing import Any, Dict, Optional

from src.pagination import MAX_BATCH_OBJECTS
from src.response_format import EXPORT_USER_STORAGE_HINT_THRESHOLD


def build_list_hint(
    *,
    complete: bool,
    fetched: int,
    total_count: int,
    filters: Dict[str, Any],
    list_kind: str = "storage",
    list_tool: Optional[str] = None,
    next_cursor: Optional[str] = None,
) -> Optional[str]:
    """Build an actionable hint for list tool responses."""
    if list_kind == "accounts":
        hint = _build_accounts_hint(
            complete=complete,
            fetched=fetched,
            total_count=total_count,
            filters=filters,
        )
    else:
        hint = _build_storage_hint(
            complete=complete,
            fetched=fetched,
            total_count=total_count,
            filters=filters,
            list_tool=list_tool,
        )

    if next_cursor:
        cursor_hint = "Pass next_cursor to fetch the next page."
        hint = append_hint(hint, cursor_hint)

    return hint


def _build_accounts_hint(
    *,
    complete: bool,
    fetched: int,
    total_count: int,
    filters: Dict[str, Any],
) -> Optional[str]:
    if complete:
        if fetched:
            return "Use nakama_get_account for full profile on a specific user id."
        return None

    remaining = max(total_count - fetched, 0)
    if not filters.get("filter"):
        return (
            f"{remaining} more account(s) exist. Add a filter (username or user id) "
            "before raising max_objects."
        )
    return (
        f"{remaining} more account(s) exist. Raise max_objects as a last resort "
        "after narrowing the filter."
    )


def _build_storage_hint(
    *,
    complete: bool,
    fetched: int,
    total_count: int,
    filters: Dict[str, Any],
    list_tool: Optional[str] = None,
) -> Optional[str]:
    parts: list[str] = []

    user_id = filters.get("user_id")
    collection = filters.get("collection")
    if user_id and not collection and not filters.get("key") and not filters.get("key_prefix"):
        parts.append(
            "Nakama may return all objects for this user with no pagination. "
            "Add collection to narrow."
        )

    if complete:
        if fetched:
            if fetched > MAX_BATCH_OBJECTS:
                batches = math.ceil(fetched / MAX_BATCH_OBJECTS)
                parts.append(
                    f"{fetched} keys returned. Call nakama_get_storage_objects in "
                    f"{batches} separate batches of up to {MAX_BATCH_OBJECTS}. "
                    "Fetch only keys you need."
                )
            else:
                parts.append(
                    "Load values with nakama_get_storage_objects (batch) or "
                    "nakama_get_storage_object."
                )

            if (
                list_tool == "nakama_list_user_storage"
                and fetched > EXPORT_USER_STORAGE_HINT_THRESHOLD
                and user_id
            ):
                parts.append(
                    "For all storage values for this user, prefer nakama_export_account "
                    "(large; use response_mode=resource)."
                )
        return " ".join(parts) if parts else None

    remaining = max(total_count - fetched, 0)
    has_user = bool(user_id)
    has_key = bool(filters.get("key") or filters.get("key_prefix"))

    if not has_user:
        parts.append(
            f"{remaining} more object(s) exist. Add user_id to narrow scope "
            "before raising max_objects."
        )
    elif not has_key:
        parts.append(
            f"{remaining} more object(s) exist. Add key or key_prefix "
            "(suffix % prefix only, e.g. 'level%') before raising max_objects."
        )
    else:
        parts.append(
            f"{remaining} more object(s) exist. Raise max_objects (max 1000) "
            "only after narrowing user_id and key filters."
        )

    return " ".join(parts) if parts else None


def append_hint(base: Optional[str], extra: Optional[str]) -> Optional[str]:
    """Combine two hint strings when both are present."""
    if base and extra:
        return f"{base} {extra}"
    return base or extra


__all__ = ["build_list_hint", "append_hint"]
