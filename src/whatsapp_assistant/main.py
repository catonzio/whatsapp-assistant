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
from .services.whatsapp.schemas import WhatsAppWebhookPayload

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


def _add_webhook_schema(app: FastAPI) -> None:
    """Document POST /webhook's request body on the OpenAPI page.

    The route reads raw bytes to verify Meta's HMAC signature before parsing
    (see `webhook.py`), so it can't declare a Pydantic body parameter the
    normal way — FastAPI would parse/validate the body ahead of that check.
    Wrapping `app.openapi()` instead lets us inject the schema after the
    full document (paths, security schemes, root_path-derived servers, etc.)
    is already built by FastAPI's own logic, then point requestBody at it.

    Pydantic's `model_json_schema()` emits nested models under a local
    `$defs` with refs like `#/$defs/WebhookValue` — valid only when that
    schema is the root document. Embedded under `requestBody.content...
    schema` in the full OpenAPI doc, those refs fail to resolve (Swagger/
    Redoc look for `$defs` at the *document* root). Hoisting the defs into
    `components.schemas` and pointing refs at `#/components/schemas/...`,
    which is where FastAPI itself puts model schemas, fixes that.
    """
    original_openapi = app.openapi

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema

        schema = original_openapi()
        payload_schema = WhatsAppWebhookPayload.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        defs = payload_schema.pop("$defs", {})
        components_schemas = schema.setdefault("components", {}).setdefault(
            "schemas", {}
        )
        components_schemas.update(defs)
        components_schemas["WhatsAppWebhookPayload"] = payload_schema

        schema["paths"]["/webhook"]["post"]["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/WhatsAppWebhookPayload"}
                }
            },
        }
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi


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
    _add_webhook_schema(app)
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
