from functools import lru_cache

from ...configs.settings import get_settings
from .handler import MessageHandler
from .whatsapp import WhatsAppClient


@lru_cache
def get_whatsapp_client() -> WhatsAppClient:
    settings = get_settings()
    return WhatsAppClient(
        token=settings.whatsapp_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        graph_url=settings.graph_url,
    )


@lru_cache
def get_message_handler() -> MessageHandler:
    from ..dependencies import get_transcription_service, get_chat_service

    settings = get_settings()
    return MessageHandler(
        whatsapp=get_whatsapp_client(),
        transcription=get_transcription_service(),
        chat_service=get_chat_service(),
        max_message_len=settings.max_message_len,
    )
