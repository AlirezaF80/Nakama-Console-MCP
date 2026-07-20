import pytest
from unittest.mock import AsyncMock

from src.tools.accounts import nakama_list_wallet_ledger


@pytest.mark.asyncio
async def test_list_wallet_ledger_sends_limit_and_returns_envelope():
    client = AsyncMock()
    client.get.return_value = {
        "items": [
            {
                "id": "46dc370e-742e-43e0-a417-5749a31ce6a1",
                "changeset": {"2": -1000},
                "metadata": {"reasons": ["spend"]},
                "update_time": "2026-07-20T13:23:56Z",
            }
        ],
        "next_cursor": "",
    }

    result = await nakama_list_wallet_ledger(
        client,
        id="09d106cf-3a7e-4e17-9e1e-39c46ebce789",
    )

    client.get.assert_awaited_once()
    path, = client.get.await_args.args
    assert path.endswith("/wallet")
    params = client.get.await_args.kwargs["params"]
    assert params["limit"] == 100
    assert "cursor" not in params

    assert result["fetched"] == 1
    assert result["complete"] is True
    assert result["next_cursor"] is None
    assert len(result["items"]) == 1
    assert result["items"][0]["changeset"] == {"2": -1000}
    assert result["hint"] is not None
    assert "nakama_get_account" in result["hint"]


@pytest.mark.asyncio
async def test_list_wallet_ledger_passes_time_filters_and_cursor():
    client = AsyncMock()
    client.get.return_value = {
        "items": [{"id": "a", "changeset": {"1": 1}}],
        "next_cursor": "older",
    }

    result = await nakama_list_wallet_ledger(
        client,
        id="u1",
        cursor="page1",
        after="2026-07-01T00:00:00Z",
        before="2026-07-20T00:00:00Z",
        max_objects=50,
    )

    params = client.get.await_args.kwargs["params"]
    assert params["limit"] == 50
    assert params["cursor"] == "page1"
    assert params["after"] == "2026-07-01T00:00:00Z"
    assert params["before"] == "2026-07-20T00:00:00Z"
    assert result["complete"] is False
    assert result["next_cursor"] == "older"
    assert "next_cursor" in (result["hint"] or "")


@pytest.mark.asyncio
async def test_list_wallet_ledger_aggregates_pages():
    client = AsyncMock()
    client.get.side_effect = [
        {
            "items": [{"id": str(i), "changeset": {}} for i in range(100)],
            "next_cursor": "p2",
        },
        {
            "items": [{"id": str(i), "changeset": {}} for i in range(100, 150)],
            "next_cursor": "",
        },
    ]

    result = await nakama_list_wallet_ledger(
        client,
        id="u1",
        max_objects=150,
    )

    assert client.get.await_count == 2
    assert result["fetched"] == 150
    assert result["complete"] is True
    assert result["next_cursor"] is None
    assert result["hint"] is not None
    assert "nakama_get_account" in result["hint"]
    assert "nakama_export_account" in result["hint"]
    # Each page requests Nakama max page size when max_objects > 100
    assert client.get.await_args_list[0].kwargs["params"]["limit"] == 100
    assert client.get.await_args_list[1].kwargs["params"]["limit"] == 100


@pytest.mark.asyncio
async def test_list_wallet_ledger_empty_complete_has_no_hint():
    client = AsyncMock()
    client.get.return_value = {"items": [], "next_cursor": ""}

    result = await nakama_list_wallet_ledger(client, id="u1")

    assert result["fetched"] == 0
    assert result["complete"] is True
    assert result["hint"] is None
