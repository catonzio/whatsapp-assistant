import json
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)

from ..configs.settings import Settings, get_settings
from ..services.dependencies import get_message_handler
from ..services.whatsapp.dependencies import get_inbound_message_store
from ..services.whatsapp.handler import MessageHandler
from ..services.whatsapp.inbound_store import InboundMessageStore
from ..services.whatsapp.signature import verify_signature

logger = logging.getLogger("whatsapp-assistant")

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    """Meta calls this once to verify the endpoint when you configure the webhook."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    handler: MessageHandler = Depends(get_message_handler),
    inbound_store: InboundMessageStore = Depends(get_inbound_message_store),
) -> Response:
    """Receive incoming messages.

    Verifies the payload actually came from Meta (HMAC signature), durably
    records every message *before* acking (so a crash after the ack can't
    lose it — see docs/architecture.md §6.2), then acks 200 immediately and
    processes in the background, because WhatsApp retries the webhook if we
    don't reply with 200 quickly.
    """
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    if not verify_signature(body, signature, settings.whatsapp_app_secret):
        logger.warning("Rejecting webhook POST with invalid/missing signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)

    new_message_ids = await inbound_store.record_all(payload)
    for message_id in new_message_ids:
        background_tasks.add_task(handler.process_stored_message, message_id)

    return Response(status_code=200)
