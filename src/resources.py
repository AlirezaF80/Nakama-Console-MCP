"""In-memory MCP resources for large Nakama export payloads."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


EXPORT_RESOURCE_SCHEME = "nakama://export"
EXPORT_CACHE_TTL_SECONDS = 15 * 60
EXPORT_CACHE_MAX_ENTRIES = 10


@dataclass
class CachedExport:
    account_id: str
    payload: bytes
    created_at: float

    @property
    def uri(self) -> str:
        return f"{EXPORT_RESOURCE_SCHEME}/{self.account_id}/{self.export_id}"

    @property
    def export_id(self) -> str:
        # last path segment from uri construction helper
        return self._export_id

    def __init__(self, account_id: str, payload: bytes, export_id: str):
        self.account_id = account_id
        self.payload = payload
        self.created_at = time.time()
        self._export_id = export_id


class ExportCache:
    """TTL-bound cache of account export JSON blobs addressable as MCP resources."""

    def __init__(
        self,
        *,
        ttl_seconds: int = EXPORT_CACHE_TTL_SECONDS,
        max_entries: int = EXPORT_CACHE_MAX_ENTRIES,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: Dict[str, CachedExport] = {}

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            uri
            for uri, entry in self._entries.items()
            if now - entry.created_at > self.ttl_seconds
        ]
        for uri in expired:
            del self._entries[uri]

    def store(self, account_id: str, data: Dict[str, Any]) -> str:
        self._purge_expired()
        while len(self._entries) >= self.max_entries:
            oldest_uri = min(self._entries, key=lambda u: self._entries[u].created_at)
            del self._entries[oldest_uri]

        export_id = uuid.uuid4().hex
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        entry = CachedExport(account_id, payload, export_id)
        self._entries[entry.uri] = entry
        return entry.uri

    def get(self, uri: str) -> Optional[CachedExport]:
        self._purge_expired()
        return self._entries.get(uri)

    def list_uris(self) -> List[str]:
        self._purge_expired()
        return list(self._entries.keys())


def register_resources(server, cache: ExportCache) -> None:
    """Register MCP resource handlers for cached account exports."""
    import mcp

    @server.list_resources()
    async def _list_resources() -> list[mcp.types.Resource]:
        return [
            mcp.types.Resource(
                uri=uri,
                name=f"Nakama account export ({uri.rsplit('/', 1)[-1][:8]})",
                description="Cached Nakama account export JSON",
                mimeType="application/json",
            )
            for uri in cache.list_uris()
        ]

    @server.read_resource()
    async def _read_resource(uri: str):
        entry = cache.get(uri)
        if entry is None:
            raise ValueError(f"Unknown or expired export resource: {uri}")
        return entry.payload.decode("utf-8")


__all__ = [
    "EXPORT_RESOURCE_SCHEME",
    "EXPORT_CACHE_TTL_SECONDS",
    "EXPORT_CACHE_MAX_ENTRIES",
    "CachedExport",
    "ExportCache",
    "register_resources",
]
