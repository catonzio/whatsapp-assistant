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
from ..services.whatsapp.handler import MessageHandler

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
    handler: MessageHandler = Depends(get_message_handler),
) -> Response:
    """Receive incoming messages. We ACK immediately and process in the background,
    because WhatsApp retries the webhook if we don't reply with 200 quickly."""
    payload = await request.json()
    background_tasks.add_task(handler.process_payload, payload)
    return Response(status_code=200)
