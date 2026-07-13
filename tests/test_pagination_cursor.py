import pytest

from src.pagination import fetch_page_once, fetch_pages


@pytest.mark.asyncio
async def test_fetch_page_once_returns_next_cursor():
    calls = {"count": 0}

    async def fetch_page(cursor):
        calls["count"] += 1
        if cursor is None:
            return {
                "objects": [{"key": "1"}],
                "total_count": 2,
                "next_cursor": "page2",
            }
        return {"objects": [{"key": "2"}], "total_count": 2}

    first = await fetch_page_once(fetch_page, items_key="objects", cursor=None)
    assert first["fetched"] == 1
    assert first["complete"] is False
    assert first["next_cursor"] == "page2"

    second = await fetch_page_once(fetch_page, items_key="objects", cursor="page2")
    assert second["fetched"] == 1
    assert second["complete"] is True
    assert second["next_cursor"] is None


@pytest.mark.asyncio
async def test_fetch_pages_exposes_next_cursor_when_truncated():
    pages = [
        {"objects": [{"key": str(i)} for i in range(100)], "total_count": 250, "next_cursor": "p2"},
        {"objects": [{"key": str(i)} for i in range(100, 200)], "total_count": 250, "next_cursor": "p3"},
    ]
    state = {"idx": 0}

    async def fetch_page(cursor):
        page = pages[state["idx"]]
        state["idx"] += 1
        return page

    envelope = await fetch_pages(fetch_page, items_key="objects", max_objects=100)
    assert envelope["fetched"] == 100
    assert envelope["complete"] is False
    assert envelope["next_cursor"] == "p2"
