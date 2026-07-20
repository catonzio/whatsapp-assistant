from functools import lru_cache

from ...configs.settings import get_settings
from ...database.session import get_sessionmaker
from .authorization import PhoneWhitelist
from .handler import MessageHandler
from .inbound_store import InboundMessageStore
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
def get_phone_whitelist() -> PhoneWhitelist:
    return PhoneWhitelist(get_sessionmaker())


@lru_cache
def get_inbound_message_store() -> InboundMessageStore:
    return InboundMessageStore(get_sessionmaker())


@lru_cache
def get_message_handler() -> MessageHandler:
    from ..dependencies import get_chat_service

    settings = get_settings()
    return MessageHandler(
        whatsapp=get_whatsapp_client(),
        chat_service=get_chat_service(),
        max_message_len=settings.max_message_len,
        authorized_users=get_phone_whitelist(),
        inbound_store=get_inbound_message_store(),
    )
