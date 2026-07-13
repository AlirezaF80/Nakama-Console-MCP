import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.config import NakamaSettings
from src.nakama_client import NakamaConsoleClient


def _settings() -> NakamaSettings:
    return NakamaSettings(
        nakama_console_url="http://127.0.0.1:7351",
        nakama_username="admin",
        nakama_password="secret",
    )


@pytest.mark.asyncio
async def test_reauthenticates_on_401_and_retries():
    client = NakamaConsoleClient(_settings())

    unauthorized = MagicMock()
    unauthorized.status_code = 401

    success = MagicMock()
    success.status_code = 200
    success.raise_for_status = MagicMock()
    success.json = MagicMock(return_value={"users": []})

    auth_response = MagicMock()
    auth_response.status_code = 200
    auth_response.json = MagicMock(return_value={"token": "fresh-token"})

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_request.side_effect = [unauthorized, success]
            mock_post.return_value = auth_response

            data = await client.get("/v2/console/account")

    assert data == {"users": []}
    assert client.is_authenticated
    assert mock_post.await_count == 1
    assert mock_request.await_count == 2

    await client.close()
