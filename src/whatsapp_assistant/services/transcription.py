import asyncio

from openai import OpenAI

# Map WhatsApp/audio mime types to a file extension so OpenAI infers the format.
MIME_TO_EXT = {
    "audio/ogg": "ogg",
    "audio/opus": "ogg",
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/aac": "aac",
    "audio/amr": "amr",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}


class TranscriptionService:
    """Wraps OpenAI audio transcription."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        # The OpenAI client is synchronous; run it off the event loop.
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes, mime_type)

    def _transcribe_sync(self, audio_bytes: bytes, mime_type: str) -> str:
        ext = MIME_TO_EXT.get(mime_type.split(";")[0].strip(), "ogg")
        transcription = self._client.audio.transcriptions.create(
            model=self._model,
            file=(f"audio.{ext}", audio_bytes, mime_type),
        )
        return transcription.text
