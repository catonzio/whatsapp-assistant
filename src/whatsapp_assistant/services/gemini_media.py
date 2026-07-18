import asyncio
import io
import logging

from google import genai
from google.genai import types

logger = logging.getLogger("whatsapp-assistant")


class GeminiMediaUploader:
    """Hands WhatsApp media to Gemini/ADK without inlining bytes or hosting
    it publicly.

    WhatsApp's media URL requires our bearer token, so the model can never
    fetch it directly. Instead we upload the bytes we already downloaded to
    Gemini's Files API: the file is stored privately under our API key/project
    (not publicly reachable) and auto-expires after 48h. We then reference it
    by URI, so it isn't re-sent as inline base64 on every model call.
    """

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    async def upload(self, data: bytes, mime_type: str) -> types.Part:
        file = await asyncio.to_thread(self._upload_sync, data, mime_type)
        return types.Part(
            file_data=types.FileData(file_uri=file.uri, mime_type=file.mime_type)
        )

    def _upload_sync(self, data: bytes, mime_type: str) -> types.File:
        return self._client.files.upload(
            file=io.BytesIO(data),
            config=types.UploadFileConfig(mime_type=mime_type),
        )
