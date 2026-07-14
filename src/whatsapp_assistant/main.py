import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from .api.waha import router as waha_router
from .api.webhook import router as webhook_router

load_dotenv()

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(
        title="WhatsApp Assistant",
        description="A WhatsApp assistant built with FastAPI and LangChain.",
        version="0.1.0",
        root_path="/whatsapp-assistant",
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
