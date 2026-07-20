from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
    database_url: str
    # Separate database, same Postgres instance, used exclusively by ADK's
    # DatabaseSessionService (its own internal schema, not modeled by us).
    agent_sessions_database_url: str

    # The agentic framework to use for the chat service.
    # Currently only "google-adk" is supported.
    agentic_framework: str = "google-adk"

    @property
    def graph_url(self) -> str:
        return f"https://graph.facebook.com/{self.graph_api_version}"


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so settings are parsed once per process."""
    return Settings()  # type: ignore[call-arg]
