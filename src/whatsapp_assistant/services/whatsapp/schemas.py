"""Pydantic models for the WhatsApp Cloud API webhook payload.

Shape reference: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples

These exist so `POST /webhook` can document its request body on the OpenAPI
page (`webhook.py` reads the raw bytes for HMAC verification before parsing,
so FastAPI can't infer the body schema from the route signature the usual
way — see `openapi_extra` in `webhook.py`).

Meta sends more fields than we act on (statuses, errors, additional message
types like location/reaction/sticker) and `handle_message` already degrades
gracefully for message types it doesn't recognize (see `handler.py`). So
every model here uses `extra="allow"` and only the fields the pipeline
actually reads are required — this documents the real shape without turning
into a strict gate that could 422 a legitimate Meta payload we haven't
modeled yet.
"""

from pydantic import BaseModel, ConfigDict, Field


class WebhookProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None


class WebhookContact(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile: WebhookProfile | None = None
    wa_id: str | None = None


class WebhookMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    display_phone_number: str | None = None
    phone_number_id: str | None = None


class WebhookTextBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    body: str


class WebhookMedia(BaseModel):
    """Shape shared by audio/image/video/document messages."""

    model_config = ConfigDict(extra="allow")

    id: str
    mime_type: str | None = None
    sha256: str | None = None
    caption: str | None = None


class WebhookMessage(BaseModel):
    """One inbound message. `from_`/`id` are required — `InboundMessageStore`
    already drops anything missing them (see `inbound_store.py`), so
    requiring them here just surfaces that same rule as a clean 422 instead
    of a silent skip."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    from_: str = Field(alias="from")
    id: str
    timestamp: str | None = None
    type: str | None = None
    text: WebhookTextBody | None = None
    audio: WebhookMedia | None = None
    image: WebhookMedia | None = None
    video: WebhookMedia | None = None
    document: WebhookMedia | None = None


class WebhookValue(BaseModel):
    model_config = ConfigDict(extra="allow")

    messaging_product: str | None = None
    metadata: WebhookMetadata | None = None
    contacts: list[WebhookContact] = Field(default_factory=list)
    messages: list[WebhookMessage] = Field(default_factory=list)


class WebhookChange(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: WebhookValue
    field: str | None = None


class WebhookEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    changes: list[WebhookChange] = Field(default_factory=list)


class WhatsAppWebhookPayload(BaseModel):
    """Top-level body of a `POST /webhook` call from Meta."""

    model_config = ConfigDict(
        extra="allow",
        # Shown as the "Example Value" on the OpenAPI page. Sender/phone-number
        # ID are real-looking but not real — masked as "XXXX" on purpose.
        json_schema_extra={
            "examples": [
                {
                    "object": "whatsapp_business_account",
                    "entry": [
                        {
                            "id": "TEST_WABA_ID",
                            "changes": [
                                {
                                    "field": "messages",
                                    "value": {
                                        "messaging_product": "whatsapp",
                                        "metadata": {
                                            "display_phone_number": "XXXX",
                                            "phone_number_id": "XXXX",
                                        },
                                        "contacts": [
                                            {
                                                "profile": {"name": "Dev Test"},
                                                "wa_id": "XXXX",
                                            }
                                        ],
                                        "messages": [
                                            {
                                                "from": "XXXX",
                                                "id": "wamid.EXAMPLE123",
                                                "timestamp": "0",
                                                "type": "text",
                                                "text": {"body": "ciao"},
                                            }
                                        ],
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    )

    object: str | None = None
    entry: list[WebhookEntry] = Field(default_factory=list)
