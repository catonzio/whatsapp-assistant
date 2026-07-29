import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file="secrets/.env", extra="ignore")

    # App metadata (used in OpenAPI docs, etc.)
    app_name: str = "whatsapp-assistant"
    app_description: str = ""
    version: str = "0.1.0"
    domain: str = "localhost"
    root_path: str = "/whatsapp-assistant"
    
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

    # Domain agents (docs/architecture.md §8). Split in two tiers to control
    # cost: the orchestrator does routing + Italian tone + vision/audio
    # reasoning on every message (needs to be a bit more capable), the three
    # domain sub-agents only do structured CRUD tool-calling (cheaper model
    # is enough).
    gemini_model_orchestrator: str = "gemini-3.1-flash"
    gemini_model_subagent: str = "gemini-3.1-flash-lite"

    # Place verification tool (§8.3, requirements.md §4.2): which provider
    # `verify_place` calls to confirm e.g. "is this actually a restaurant?"
    # before auto-creating a category. "google" (Places API, paid per call)
    # or "osm" (Nominatim, free/rate-limited) — swappable without code
    # changes if Google Places costs eat into the monthly budget.
    # place_lookup_provider: str = "google"
    place_lookup_provider: str = "osm"
    google_maps_api_key: str | None = None

    # Link handling (§8.3, requirements.md §4.5): by default the cataloging
    # agent asks the user for confirmation before fetching a link's metadata.
    # Set to True to fetch immediately without asking.
    link_auto_fetch: bool = False

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
