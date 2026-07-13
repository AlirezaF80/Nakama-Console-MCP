import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from src.config import NakamaSettings

logger = logging.getLogger(__name__)


class NakamaConsoleClient:
    """Async client for Nakama Console API (read-only).

    Usage:
        settings = NakamaSettings()
        client = NakamaConsoleClient(settings)
        await client.authenticate()
        data = await client.get('/v2/console/account')
    """

    def __init__(self, settings: NakamaSettings, timeout: float = 10.0):
        self.settings = settings
        self.base_url = settings.nakama_console_url.rstrip("/")
        self._token: Optional[str] = None
        self._client = httpx.AsyncClient(timeout=timeout)
        self._lock = asyncio.Lock()

    async def authenticate(self, *, force: bool = False) -> str:
        """Authenticate the console user and store the JWT token.

        When force is True, ignore any cached token and fetch a new one
        (used after a 401 to reauth).
        """
        async with self._lock:
            if self._token and not force:
                return self._token
            url = f"{self.base_url}/v2/console/authenticate"
            payload = {"username": self.settings.nakama_username, "password": self.settings.nakama_password}
            try:
                resp = await self._client.post(url, json=payload)
            except Exception:
                logger.exception("Failed to reach Nakama Console authenticate endpoint")
                raise
            if resp.status_code != 200:
                logger.error("Authentication failed: %s %s", resp.status_code, resp.text)
                raise RuntimeError(f"Authentication failed: {resp.status_code} {resp.text}")
            data = resp.json()
            token = data.get("token")
            if not token:
                raise RuntimeError("Authentication succeeded but no token returned")
            self._token = token
            logger.info("Authenticated to Nakama Console; token cached")
            return self._token

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    def _auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """HTTP request with automatic authentication and retry on 401 once."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        kwargs: Dict[str, Any] = {"headers": self._auth_headers()}
        if params is not None:
            kwargs["params"] = params
        if json_data is not None:
            kwargs["json"] = json_data

        resp = await self._client.request(method, url, **kwargs)
        if resp.status_code == 401:
            logger.info("Token unauthorized, reauthenticating and retrying %s %s", method, path)
            await self.authenticate(force=True)
            kwargs["headers"] = self._auth_headers()
            resp = await self._client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET request with automatic authentication and retry on 401 once."""
        return await self._request("GET", path, params=params or {})

    async def post(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        """POST request with automatic authentication and retry on 401 once."""
        return await self._request("POST", path, json_data=json_data or {})

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["NakamaConsoleClient"]
