import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from .api.waha import router as waha_router
from .api.webhook import router as webhook_router
from .services.dependencies import get_inbound_message_store, get_message_handler
from .services.whatsapp.recovery import recover_unfinished_messages

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-assistant")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        await recover_unfinished_messages(
            get_message_handler(), get_inbound_message_store()
        )
    except Exception:
        # Never let a recovery hiccup (e.g. DB briefly unreachable) block startup.
        logger.exception(
            "Startup recovery of unfinished inbound messages failed; continuing"
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="WhatsApp Assistant",
        description="A WhatsApp assistant built with FastAPI and LangChain.",
        version="0.1.0",
        root_path="/whatsapp-assistant",
        lifespan=lifespan,
    )
    app.include_router(webhook_router)
    app.include_router(waha_router)
    return app


app = create_app()


def main() -> None:
    """Console entrypoint mirroring the VS Code launch config
    (`fastapi dev src/whatsapp_assistant/main.py --host 0.0.0.0 --port 8000`)."""
    import uvicorn

    uvicorn.run(
        "whatsapp_assistant.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
