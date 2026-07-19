from functools import lru_cache

from .config import get_settings
from .services.adk_chat_service import ADKChatService, build_runner
from .services.chat_service import ChatService
from .services.handler import MessageHandler
from .services.transcription import TranscriptionService
from .services.whatsapp import WhatsAppClient


@lru_cache
def get_whatsapp_client() -> WhatsAppClient:
    settings = get_settings()
    return WhatsAppClient(
        token=settings.whatsapp_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        graph_url=settings.graph_url,
    )


@lru_cache
def get_transcription_service() -> TranscriptionService:
    settings = get_settings()
    return TranscriptionService(
        api_key=settings.openai_api_key,
        model=settings.transcription_model,
    )


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    if settings.agentic_framework == "google-adk":
        return ADKChatService(build_runner(settings))
    raise ValueError(f"Unsupported agentic framework: {settings.agentic_framework}")


@lru_cache
def get_message_handler() -> MessageHandler:
    settings = get_settings()
    return MessageHandler(
        whatsapp=get_whatsapp_client(),
        transcription=get_transcription_service(),
        chat_service=get_chat_service(),
        max_message_len=settings.max_message_len,
    )
