import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from .api.webhook import router as webhook_router

load_dotenv()

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="WhatsApp Assistant")
    app.include_router(webhook_router)
    return app


app = create_app()
