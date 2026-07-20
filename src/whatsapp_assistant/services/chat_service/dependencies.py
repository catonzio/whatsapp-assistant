from functools import lru_cache

from ...configs.settings import get_settings
from .chat_service import ChatService
from .impls.adk_chat_service import ADKChatService, build_runner


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    if settings.agentic_framework == "google-adk":
        return ADKChatService(build_runner(settings))
    raise ValueError(f"Unsupported agentic framework: {settings.agentic_framework}")
