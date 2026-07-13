from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

class NakamaSettings(BaseSettings):
    """Configuration for Nakama Console connection.

    Environment variables (via .env or system env):
      - NAKAMA_NAKAMA_CONSOLE_URL
      - NAKAMA_NAKAMA_USERNAME
      - NAKAMA_NAKAMA_PASSWORD
    """

    nakama_console_url: str
    nakama_username: str
    nakama_password: str

    model_config = SettingsConfigDict(
        env_prefix="NAKAMA_",
        env_file_encoding="utf-8",
    )


def load_settings(env_file: Optional[Path] = None) -> NakamaSettings:
    """Load settings from process env, optionally seeding from an env file first."""
    candidates = [env_file, ENV_FILE]
    for candidate in candidates:
        if candidate and candidate.exists():
            load_dotenv(candidate, override=True)
            break
    return NakamaSettings()
