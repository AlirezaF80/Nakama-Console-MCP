"""Server-side auto-pagination for Nakama Console list endpoints."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

DEFAULT_MAX_OBJECTS = 100
MAX_OBJECTS_HARD_LIMIT = 1000

FetchPage = Callable[[Optional[str]], Awaitable[Dict[str, Any]]]


def clamp_max_objects(max_objects: int) -> int:
    """Clamp max_objects to [1, MAX_OBJECTS_HARD_LIMIT]."""
    return max(1, min(int(max_objects), MAX_OBJECTS_HARD_LIMIT))


async def fetch_pages(
    fetch_page: FetchPage,
    *,
    items_key: str,
    max_objects: int,
) -> Dict[str, Any]:
    """Fetch Console list pages until max_objects or exhaustion.

    Returns an envelope with items under ``items_key``, plus ``total_count``,
    ``fetched``, and ``complete``. Nakama cursors stay internal.
    """
    limit = clamp_max_objects(max_objects)
    items: List[Any] = []
    total_count: Optional[int] = None
    cursor: Optional[str] = None
    complete = True

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

        next_cursor = page.get("next_cursor") or None
        if isinstance(next_cursor, str) and not next_cursor.strip():
            next_cursor = None

        if len(items) >= limit:
            took_partial = len(page_items) > remaining
            complete = not took_partial and not next_cursor
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
    }


__all__ = [
    "DEFAULT_MAX_OBJECTS",
    "MAX_OBJECTS_HARD_LIMIT",
    "clamp_max_objects",
    "fetch_pages",
]
