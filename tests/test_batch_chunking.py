import asyncio
from unittest.mock import AsyncMock

import pytest

from src.tools.storage import nakama_get_storage_objects


@pytest.mark.asyncio
async def test_batch_chunking_preserves_order():
    client = AsyncMock()
    call_count = 0

    async def fake_get(path):
        nonlocal call_count
        call_count += 1
        parts = path.strip("/").split("/")
        key = parts[-2]
        return {"collection": "c", "key": key, "user_id": "u", "value": key}

    client.get = fake_get

    objects = [
        {"collection": "c", "key": str(i), "user_id": "u"}
        for i in range(120)
    ]
    result = await nakama_get_storage_objects(client, objects)

    assert result["requested"] == 120
    assert result["chunks"] == 3
    assert result["fetched"] == 120
    assert result["failed"] == 0
    assert len(result["results"]) == 120
    assert [r["key"] for r in result["results"]] == [str(i) for i in range(120)]
    assert call_count == 120
