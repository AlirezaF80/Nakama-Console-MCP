from pydantic_settings import BaseSettings, SettingsConfigDict

class NakamaSettings(BaseSettings):
    """Configuration for Nakama Console connection.

    Environment variables (via .env or system env):
      - NAKAMA_NAKAMA_CONSOLE_URL
      - NAKAMA_NAKAMA_USERNAME
      - NAKAMA_NAKAMA_PASSWORD
      - NAKAMA_NAKAMA_HTTP_KEY (optional)
    """

    nakama_console_url: str
    nakama_username: str
    nakama_password: str
    nakama_http_key: str = "defaultkey"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NAKAMA_",
        env_file_encoding="utf-8",
    )


def load_settings() -> NakamaSettings:
    return NakamaSettings()
