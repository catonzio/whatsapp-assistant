import logging
import traceback
from typing import TypedDict

from whatsapp_assistant.database.models.inbound_message import InboundMessage

from ..chat_service.chat_service import ChatService
from ..chat_service.schemas import Attachment, ChatMessage
from .authorization import PhoneWhitelist
from .inbound_store import InboundMessageStore
from .whatsapp import WhatsAppClient

logger = logging.getLogger("whatsapp-assistant")


class WhatsAppMessage(TypedDict, total=False):
    """Typed structure for WhatsApp webhook message payload."""

    from_: str
    type: str
    text: dict[str, str]
    audio: dict[str, str]
    image: dict[str, str]
    video: dict[str, str]
    document: dict[str, str]
    caption: str


class MessageHandler:
    """Orchestrates incoming webhook payloads: message -> parse -> agent -> reply.

    Durability/idempotency (recording the message, deduping, crash recovery)
    lives one layer up, in `InboundMessageStore` — this class only knows how
    to turn *one* already-persisted WhatsApp message dict into a reply.
    """

    def __init__(
        self,
        whatsapp: WhatsAppClient,
        chat_service: ChatService,
        max_message_len: int,
        authorized_users: PhoneWhitelist,
        inbound_store: InboundMessageStore,
    ) -> None:
        self._whatsapp = whatsapp
        self._chat_service = chat_service
        self._max_message_len = max_message_len
        self._authorized_users = authorized_users
        self._inbound_store = inbound_store

    async def process_stored_message(self, message_id: int) -> None:
        """Process a message already durably recorded by `InboundMessageStore`.

        Used both by the live webhook path and by `recover_unfinished_messages`
        at startup (see docs/architecture.md §6.2) — both just need a message
        id, so a previous run's leftover rows replay through the exact same
        path as a fresh delivery.
        """
        row: InboundMessage | None = await self._inbound_store.fetch(message_id)
        if row is None:
            logger.warning("Stored message %s no longer exists, skipping", message_id)
            return

        await self._inbound_store.mark_processing(message_id)
        try:
            await self.handle_message(row.payload)
        except Exception:
            logger.exception(
                "Unrecoverable error processing stored message %s", message_id
            )
            await self._inbound_store.mark_failed(
                message_id, traceback.format_exc(limit=5)
            )
            return
        await self._inbound_store.mark_done(message_id)

    async def handle_message(self, message: dict) -> None:
        sender = message.get("from")
        if not sender:
            return

        if not await self._authorized_users.is_authorized(sender):
            logger.warning("Ignoring message from unauthorized number %s", sender)
            return

        sender, chat_message = await self._parse_message(message)
        if chat_message is None:
            return

        try:
            reply = await self._chat_service.send_async(chat_message)
        except Exception:
            logger.exception("Chat service failed for %s", sender)
            await self._whatsapp.send_text(
                sender, "Ops, qualcosa è andato storto. Riprova! 😕"
            )
            return

        await self._whatsapp.send_text(sender, reply[: self._max_message_len])

    async def _parse_message(self, message: dict) -> tuple[str, ChatMessage | None]:
        """Parse a WhatsApp message payload into a ChatMessage object.

        Extracts sender, text content, and media attachments (audio, image,
        video, document) — all forwarded as attachments alongside any caption,
        for the agent's multimodal tools to handle directly
        (docs/architecture.md §5); audio is not transcribed separately. Sends
        user-facing error messages for unsupported message types.

        Args:
            message: A WhatsApp message dict from the webhook payload

        Returns:
            Tuple of (sender, chat_message). chat_message is None if the message
            type is unsupported (error already sent to user).
        """
        sender = message["from"]
        msg_type = message.get("type")
        text = ""
        attachments: list[Attachment] = []

        if msg_type == "text":
            text = message["text"]["body"]
        elif msg_type == "audio":
            media_id = message["audio"]["id"]
            attachment = await self._download_attachment(media_id, "audio")
            if attachment:
                attachments.append(attachment)
        elif msg_type == "image":
            media_id = message["image"]["id"]
            attachment = await self._download_attachment(media_id, "image")
            if attachment:
                attachments.append(attachment)
            text = message.get("caption", "")
        elif msg_type == "video":
            media_id = message["video"]["id"]
            attachment = await self._download_attachment(media_id, "video")
            if attachment:
                attachments.append(attachment)
            text = message.get("caption", "")
        elif msg_type == "document":
            media_id = message["document"]["id"]
            attachment = await self._download_attachment(media_id, "document")
            if attachment:
                attachments.append(attachment)
            text = message.get("caption", "")
        else:
            await self._whatsapp.send_text(
                sender, "Per ora gestisco solo testo e messaggi vocali! 🙂"
            )
            return sender, None

        return sender, ChatMessage(user_id=sender, text=text, attachments=attachments)

    async def _download_attachment(
        self, media_id: str, media_type: str
    ) -> Attachment | None:
        """Download a media attachment from WhatsApp.

        Args:
            media_id: The WhatsApp media ID
            media_type: Type of media (audio, image, video, document)

        Returns:
            An Attachment object or None if download failed (error already logged).
        """
        try:
            data, mime_type = await self._whatsapp.download_media(media_id)
            filename = f"attachment.{mime_type.split('/')[-1]}"
            return Attachment(filename=filename, data=data, mime_type=mime_type)
        except Exception:
            logger.exception(
                "Failed to download attachment %s (type: %s)", media_id, media_type
            )
            return None
