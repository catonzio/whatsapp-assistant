import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-assistant")

GRAPH_API_VERSION = "v21.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Access token from the Meta app (WhatsApp > API Setup).
WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
# The "Phone number ID" shown in the same panel (NOT the phone number itself).
PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
# Any string you choose; must match what you enter in the Meta webhook config.
VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]

# WhatsApp text messages have a 4096-char body limit.
MAX_MESSAGE_LEN = 4096

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

client = OpenAI()
app = FastAPI()


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}


@app.get("/webhook")
async def verify_webhook(request: Request) -> Response:
    """Meta calls this once to verify the endpoint when you configure the webhook."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> Response:
    """Receive incoming messages. We ACK immediately and process in the background,
    because WhatsApp retries the webhook if we don't reply with 200 quickly."""
    payload = await request.json()
    background_tasks.add_task(process_payload, payload)
    return Response(status_code=200)


async def process_payload(payload: dict) -> None:
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    await handle_message(message)
    except Exception:
        logger.exception("Failed to process webhook payload")


async def handle_message(message: dict) -> None:
    sender = message["from"]
    msg_type = message.get("type")

    if msg_type != "audio":
        await send_text(
            sender,
            "Inviami un messaggio vocale e te lo trascrivo! 🎙️",
        )
        return

    logger.info("Received audio message from %s", sender)
    media_id = message["audio"]["id"]

    try:
        audio_bytes, mime_type = await download_media(media_id)
        transcription = await asyncio.to_thread(transcribe, audio_bytes, mime_type)
    except Exception:
        logger.exception("Transcription failed for %s", sender)
        await send_text(
            sender, "Ops, non sono riuscito a trascrivere l'audio. Riprova! 😕"
        )
        return

    reply = transcription.strip() or "(nessun parlato rilevato)"
    await send_text(sender, reply[:MAX_MESSAGE_LEN])


async def download_media(media_id: str) -> tuple[bytes, str]:
    """WhatsApp media download is two steps: resolve the media ID to a temporary
    URL, then fetch the bytes. Both requests need the access token."""
    async with httpx.AsyncClient(timeout=30) as http:
        meta_resp = await http.get(f"{GRAPH_URL}/{media_id}", headers=_auth_headers())
        meta_resp.raise_for_status()
        info = meta_resp.json()

        media_resp = await http.get(info["url"], headers=_auth_headers())
        media_resp.raise_for_status()
        return media_resp.content, info.get("mime_type", "audio/ogg")


def transcribe(audio_bytes: bytes, mime_type: str) -> str:
    ext = MIME_TO_EXT.get(mime_type.split(";")[0].strip(), "ogg")
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=(f"audio.{ext}", audio_bytes, mime_type),
    )
    return transcription.text


async def send_text(to: str, body: str) -> None:
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            f"{GRAPH_URL}/{PHONE_NUMBER_ID}/messages",
            headers={**_auth_headers(), "Content-Type": "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            },
        )
        if resp.is_error:
            logger.error("Failed to send message: %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
