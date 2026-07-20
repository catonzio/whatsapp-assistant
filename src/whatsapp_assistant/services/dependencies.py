from functools import lru_cache

from ..configs.settings import get_settings
from .transcription import TranscriptionService
from .chat_service.dependencies import get_chat_service
from .whatsapp.dependencies import get_whatsapp_client, get_message_handler

__all__ = [
    "get_transcription_service",
    "get_chat_service",
    "get_whatsapp_client",
    "get_message_handler",
]


@lru_cache
def get_transcription_service() -> TranscriptionService:
    settings = get_settings()
    return TranscriptionService(
        api_key=settings.openai_api_key,
        model=settings.transcription_model,
    )
