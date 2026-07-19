import logging

from .chat_service import ChatMessage, ChatService
from .transcription import TranscriptionService
from .whatsapp import WhatsAppClient

logger = logging.getLogger("whatsapp-assistant")


class MessageHandler:
    """Orchestrates incoming webhook payloads: (audio -> transcription ->) agent -> reply."""

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
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for message in value.get("messages", []):
                        await self.handle_message(message)
        except Exception:
            logger.exception("Failed to process webhook payload")

    async def handle_message(self, message: dict) -> None:
        sender = message["from"]
        msg_type = message.get("type")

        if msg_type == "text":
            text = message["text"]["body"]
        elif msg_type == "audio":
            text = await self._handle_audio(sender, message)
            if text is None:
                return
        else:
            await self._whatsapp.send_text(
                sender, "Per ora gestisco solo testo e messaggi vocali! 🙂"
            )
            return

        try:
            reply = await self._chat_service.send_async(
                ChatMessage(user_id=sender, text=text)
            )
        except Exception:
            logger.exception("Chat service failed for %s", sender)
            await self._whatsapp.send_text(
                sender, "Ops, qualcosa è andato storto. Riprova! 😕"
            )
            return

        await self._whatsapp.send_text(sender, reply[: self._max_message_len])

    async def _handle_audio(self, sender: str, message: dict) -> str | None:
        """Download and transcribe an audio message. Returns None if a reply was
        already sent (transcription failed or no speech detected)."""
        logger.info("Received audio message from %s", sender)
        media_id = message["audio"]["id"]

        try:
            audio_bytes, mime_type = await self._whatsapp.download_media(media_id)
            transcription = await self._transcription.transcribe(audio_bytes, mime_type)
        except Exception:
            logger.exception("Transcription failed for %s", sender)
            await self._whatsapp.send_text(
                sender, "Ops, non sono riuscito a trascrivere l'audio. Riprova! 😕"
            )
            return None

        text = transcription.strip()
        if not text:
            await self._whatsapp.send_text(
                sender, "Non ho rilevato parlato nell'audio, riprova! 🎙️"
            )
            return None
        return text
