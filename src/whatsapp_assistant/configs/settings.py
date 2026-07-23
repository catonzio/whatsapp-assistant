import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file="secrets/.env", extra="ignore")

    # Secrets / API credentials
    # Access token from the Meta app (WhatsApp > API Setup).
    whatsapp_token: str
    # The "Phone number ID" shown in the same panel (NOT the phone number itself).
    whatsapp_phone_number_id: str
    # Any string you choose; must match what you enter in the Meta webhook config.
    whatsapp_verify_token: str
    # App secret from the Meta app (Settings > Basic). Used to verify the
    # X-Hub-Signature-256 header on every POST /webhook so payloads that
    # didn't actually come from Meta are rejected instead of processed.
    whatsapp_app_secret: str

    # Used both by GeminiMediaUploader and, indirectly, by ADK/google-genai
    # (which reads the GEMINI_API_KEY env var already populated by load_dotenv()).
    gemini_api_key: str

    # Tunables (sensible defaults)
    graph_api_version: str = "v21.0"
    # WhatsApp text messages have a 4096-char body limit.
    max_message_len: int = 4096

    # Postgres connection for application data (items, categories, reminders,
    # lists, users). Async driver (asyncpg) required. No default on purpose:
    # must be set explicitly via .env, never fall back to weak credentials.
    database_host: str
    database_port: int
    database_user: str
    database_password: str
    database_db: str
    database_db_agent_sessions: str

    database_protocol: str

    # The agentic framework to use for the chat service.
    # Currently only "google-adk" is supported.
    agentic_framework: str = "google-adk"
    
    # The model to use for the root agent. Currently only Gemini is supported.
    gemini_model: str = "gemini-3.1-flash-lite"

    @property
    def graph_url(self) -> str:
        return f"https://graph.facebook.com/{self.graph_api_version}"

    @property
    def database_url(self) -> str:
        return (
            f"{self.database_protocol}://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_db}"
        )

    @property
    def agent_sessions_database_url(self) -> str:
        """
        Separate database, same db instance, used exclusively by ADK's
        DatabaseSessionService (its own internal schema, not modeled by us).
        """
        return (
            f"{self.database_protocol}://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_db_agent_sessions}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings are parsed once per process.

    Also mirrors gemini_api_key into the process environment: google-genai/ADK
    reads GEMINI_API_KEY directly from os.environ, but pydantic_settings only
    populates the Settings object's fields, not the environment itself.
    Entrypoints that don't call load_dotenv() first (e.g. `adk web`, which
    imports an agent module directly) would otherwise see no API key.
    """
    settings = Settings()  # type: ignore[call-arg]
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)
    return settings
