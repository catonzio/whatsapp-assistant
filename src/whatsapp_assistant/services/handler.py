import logging

from .transcription import TranscriptionService
from .whatsapp import WhatsAppClient

logger = logging.getLogger("whatsapp-assistant")


class MessageHandler:
    """Orchestrates incoming webhook payloads: audio -> transcription -> reply."""

    def __init__(
        self,
        whatsapp: WhatsAppClient,
        transcription: TranscriptionService,
        max_message_len: int,
    ) -> None:
        self._whatsapp = whatsapp
        self._transcription = transcription
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

        if msg_type != "audio":
            await self._whatsapp.send_text(
                sender, "Inviami un messaggio vocale e te lo trascrivo! 🎙️"
            )
            return

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
            return

        reply = transcription.strip() or "(nessun parlato rilevato)"
        await self._whatsapp.send_text(sender, reply[: self._max_message_len])
