import json
import logging
from typing import TypedDict

from .chat_service import Attachment, ChatMessage, ChatService
from .transcription import TranscriptionService
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
    """Orchestrates incoming webhook payloads: message -> parse -> agent -> reply."""

    def __init__(
        self,
        whatsapp: WhatsAppClient,
        transcription: TranscriptionService,
        chat_service: ChatService,
        max_message_len: int,
    ) -> None:
        self._whatsapp = whatsapp
        self._transcription = transcription
        self._chat_service = chat_service
        self._max_message_len = max_message_len

    async def process_payload(self, payload: dict) -> None:
        try:
            logger.info(
                "Processing webhook payload:\n%s", json.dumps(payload, indent=2)
            )
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for message in value.get("messages", []):
                        await self.handle_message(message)
        except Exception:
            logger.exception("Failed to process webhook payload")

    async def _parse_message(self, message: dict) -> tuple[str, ChatMessage | None]:
        """Parse a WhatsApp message payload into a ChatMessage object.

        Extracts sender, text content, and media attachments (audio, image, video, document).
        Sends user-facing error messages for unsupported message types.

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
            audio_bytes, mime_type = await self._whatsapp.download_media(media_id)
            # Generate a simple filename based on media type and a generic name
            filename = f"attachment.{mime_type.split('/')[-1]}"
            return Attachment(filename=filename, data=audio_bytes, mime_type=mime_type)
        except Exception:
            logger.exception(
                "Failed to download attachment %s (type: %s)", media_id, media_type
            )
            return None

    async def handle_message(self, message: dict) -> None:
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
