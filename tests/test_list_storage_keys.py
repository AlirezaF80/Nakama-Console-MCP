import pytest
from unittest.mock import AsyncMock, patch

from src.tools.storage import nakama_list_storage_keys


@pytest.mark.asyncio
async def test_list_storage_keys_projects_metadata():
    client = AsyncMock()

    async def fake_list_storage(*args, **kwargs):
        return {
            "objects": [
                {"collection": "FG", "key": "44", "user_id": "u1", "version": "v1"},
                {"collection": "FG", "key": "681", "user_id": "u1", "version": "v2"},
            ],
            "total_count": 2,
            "fetched": 2,
            "complete": True,
        }

    with patch("src.tools.storage._list_storage_envelope", side_effect=fake_list_storage):
        result = await nakama_list_storage_keys(
            client,
            collection="FG",
            user_id="u1",
        )

    assert result["keys"] == [
        {"key": "44", "user_id": "u1"},
        {"key": "681", "user_id": "u1"},
    ]
    assert result["total_count"] == 2
    assert result["complete"] is True
    assert "hint" in result
