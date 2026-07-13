"""Hint builders for list tool response envelopes."""

from typing import Any, Dict, Optional


def build_list_hint(
    *,
    complete: bool,
    fetched: int,
    total_count: int,
    filters: Dict[str, Any],
    list_kind: str = "storage",
) -> Optional[str]:
    """Build an actionable hint for list tool responses."""
    if list_kind == "accounts":
        return _build_accounts_hint(
            complete=complete,
            fetched=fetched,
            total_count=total_count,
            filters=filters,
        )
    return _build_storage_hint(
        complete=complete,
        fetched=fetched,
        total_count=total_count,
        filters=filters,
    )


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
) -> Optional[str]:
    if complete:
        if fetched:
            return "Load values with nakama_get_storage_objects (batch) or nakama_get_storage_object."
        return None

    remaining = max(total_count - fetched, 0)
    has_user = bool(filters.get("user_id"))
    has_key = bool(filters.get("key") or filters.get("key_prefix"))

    if not has_user:
        return (
            f"{remaining} more object(s) exist. Add user_id to narrow scope "
            "before raising max_objects."
        )
    if not has_key:
        return (
            f"{remaining} more object(s) exist. Add key or key_prefix "
            "(suffix % prefix only, e.g. 'level%') before raising max_objects."
        )
    return (
        f"{remaining} more object(s) exist. Raise max_objects (max 1000) "
        "only after narrowing user_id and key filters."
    )


def append_hint(base: Optional[str], extra: Optional[str]) -> Optional[str]:
    """Combine two hint strings when both are present."""
    if base and extra:
        return f"{base} {extra}"
    return base or extra


__all__ = ["build_list_hint", "append_hint"]
