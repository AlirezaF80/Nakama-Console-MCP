from typing import Any, Dict, Optional

from src.config import NakamaSettings
from src.envelopes import dump_envelope
from src.models import StatusEnvelope
from src.nakama_client import NakamaConsoleClient


def _extract_timestamp(status_data: Dict[str, Any]) -> Optional[str]:
    timestamp = status_data.get("timestamp")
    if isinstance(timestamp, dict):
        return timestamp.get("seconds") or timestamp.get("nanos")
    if isinstance(timestamp, str):
        return timestamp
    return None


async def nakama_status(client: NakamaConsoleClient, settings: NakamaSettings) -> Dict[str, Any]:
    """Return environment identity and optional Nakama node status."""
    result: Dict[str, Any] = {
        "console_url": settings.nakama_console_url,
        "authenticated": client.is_authenticated,
        "read_only": True,
        "nodes": [],
        "timestamp": None,
        "hint": None,
    }

    try:
        status_data = await client.get("/v2/console/status")
        if isinstance(status_data, dict):
            nodes = status_data.get("nodes")
            if isinstance(nodes, list):
                result["nodes"] = nodes
            result["timestamp"] = _extract_timestamp(status_data)
    except Exception as e:
        result["hint"] = f"Status endpoint unavailable: {e}"

    return dump_envelope(StatusEnvelope, result)


__all__ = ["nakama_status"]
