"""Server-side auto-pagination for Nakama Console list endpoints."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

DEFAULT_MAX_OBJECTS = 100
MAX_OBJECTS_HARD_LIMIT = 1000
MAX_BATCH_OBJECTS = 50

FetchPage = Callable[[Optional[str]], Awaitable[Dict[str, Any]]]


def clamp_max_objects(max_objects: int) -> int:
    """Clamp max_objects to [1, MAX_OBJECTS_HARD_LIMIT]."""
    return max(1, min(int(max_objects), MAX_OBJECTS_HARD_LIMIT))


def _normalize_next_cursor(page: Dict[str, Any]) -> Optional[str]:
    next_cursor = page.get("next_cursor") or None
    if isinstance(next_cursor, str) and not next_cursor.strip():
        return None
    return next_cursor


async def fetch_page_once(
    fetch_page: FetchPage,
    *,
    items_key: str,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch a single Nakama list page and expose next_cursor to the client."""
    page = await fetch_page(cursor)
    if not isinstance(page, dict):
        page = {}

    raw_total = page.get("total_count")
    total_count = int(raw_total) if raw_total is not None else 0

    page_items = page.get(items_key) or []
    if not isinstance(page_items, list):
        page_items = []

    next_cursor = _normalize_next_cursor(page)
    return {
        items_key: page_items,
        "total_count": total_count,
        "fetched": len(page_items),
        "complete": next_cursor is None,
        "next_cursor": next_cursor,
    }


async def fetch_pages(
    fetch_page: FetchPage,
    *,
    items_key: str,
    max_objects: int,
) -> Dict[str, Any]:
    """Fetch Console list pages until max_objects or exhaustion."""
    limit = clamp_max_objects(max_objects)
    items: List[Any] = []
    total_count: Optional[int] = None
    cursor: Optional[str] = None
    complete = True
    next_cursor_out: Optional[str] = None

    while True:
        page = await fetch_page(cursor)
        if not isinstance(page, dict):
            page = {}

        if total_count is None:
            raw_total = page.get("total_count")
            total_count = int(raw_total) if raw_total is not None else 0

        page_items = page.get(items_key) or []
        if not isinstance(page_items, list):
            page_items = []

        remaining = limit - len(items)
        items.extend(page_items[:remaining])

        next_cursor = _normalize_next_cursor(page)

        if len(items) >= limit:
            took_partial = len(page_items) > remaining
            complete = not took_partial and not next_cursor
            if not complete and next_cursor and not took_partial:
                next_cursor_out = next_cursor
            break

        if not next_cursor:
            complete = True
            break

        cursor = next_cursor

    return {
        items_key: items,
        "total_count": total_count if total_count is not None else 0,
        "fetched": len(items),
        "complete": complete,
        "next_cursor": next_cursor_out,
    }


__all__ = [
    "DEFAULT_MAX_OBJECTS",
    "MAX_OBJECTS_HARD_LIMIT",
    "MAX_BATCH_OBJECTS",
    "clamp_max_objects",
    "fetch_page_once",
    "fetch_pages",
]
