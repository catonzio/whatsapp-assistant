import logging
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI

from whatsapp_assistant.configs.settings import get_settings

from .api.waha import router as waha_router
from .api.webhook import router as webhook_router
from .interfaces import cli
from .services.dependencies import get_inbound_message_store, get_message_handler
from .services.whatsapp.recovery import recover_unfinished_messages

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-assistant")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
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
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.version,
        root_path=settings.root_path,
        lifespan=lifespan,
    )
    app.include_router(webhook_router)
    app.include_router(waha_router)
    return app


def run_webserver(host: str, port: int, reload: bool) -> None:
    import uvicorn

    uvicorn.run(
        "whatsapp_assistant.main:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main() -> None:
    """Console entrypoint mirroring the VS Code launch config
    (`fastapi dev src/whatsapp_assistant/main.py --host 0.0.0.0 --port 8000`).

    Requires exactly one of --cli or --webserver.
    """
    parser = ArgumentParser(description="WhatsApp Assistant")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--cli", action="store_true", help="Run the interactive dev CLI"
    )
    mode_group.add_argument(
        "--webserver", action="store_true", help="Run the FastAPI/uvicorn server"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind the webserver to (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind the webserver to (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (dev only)",
    )
    cli.add_arguments(parser)
    args = parser.parse_args()

    if args.cli:
        cli.run(args)
    elif args.webserver:
        run_webserver(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
