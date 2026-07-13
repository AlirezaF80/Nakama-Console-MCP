import json
import pytest
from types import SimpleNamespace

from src.resources import ExportCache
from src.response_format import EXPORT_INLINE_MAX_BYTES
from src.tools.accounts import nakama_export_account


@pytest.mark.asyncio
async def test_export_auto_uses_resource_for_large_payload():
    client = SimpleNamespace()
    cache = ExportCache()

    large_value = "x" * (EXPORT_INLINE_MAX_BYTES + 1)
    data = {"objects": [{"value": large_value}]}

    async def fake_get(path):
        return data

    client.get = fake_get

    result = await nakama_export_account(
        client,
        "user-1",
        response_mode="auto",
        export_cache=cache,
    )

    content, structured = result
    assert len(content) == 2
    assert structured["response_mode"] == "resource"
    assert str(content[1].uri).startswith("nakama://export/user-1/")
    assert cache.get(str(content[1].uri)) is not None
    assert structured["resource_uri"] == str(content[1].uri)


@pytest.mark.asyncio
async def test_export_inline_for_small_payload():
    client = SimpleNamespace()
    cache = ExportCache()

    async def fake_get(path):
        return {"objects": [{"value": "small"}]}

    client.get = fake_get

    result = await nakama_export_account(
        client,
        "user-1",
        response_mode="auto",
        export_cache=cache,
    )

    assert isinstance(result, dict)
    assert result["response_mode"] == "inline"
    assert result["objects"][0]["value"] == "small"
