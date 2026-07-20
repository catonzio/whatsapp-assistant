import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from whatsapp_assistant.configs.settings import get_settings
from whatsapp_assistant.main import create_app
from whatsapp_assistant.services.dependencies import get_inbound_message_store
from whatsapp_assistant.services.whatsapp.dependencies import get_message_handler

VERIFY_TOKEN = "test-verify-token"
APP_SECRET = "test-app-secret"


def _sign(body: bytes, secret: str = APP_SECRET) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture
def handler() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def inbound_store() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(handler: AsyncMock, inbound_store: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        whatsapp_verify_token=VERIFY_TOKEN, whatsapp_app_secret=APP_SECRET
    )
    app.dependency_overrides[get_message_handler] = lambda: handler
    app.dependency_overrides[get_inbound_message_store] = lambda: inbound_store
    return TestClient(app)


def _post_signed(client: TestClient, payload: dict, secret: str = APP_SECRET):
    body = json.dumps(payload).encode()
    headers = {
        "content-type": "application/json",
        "x-hub-signature-256": _sign(body, secret),
    }
    return client.post("/webhook", content=body, headers=headers)


def test_verify_webhook_success(client: TestClient):
    resp = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "31415",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "31415"


def test_verify_webhook_wrong_token(client: TestClient):
    resp = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "31415",
        },
    )
    assert resp.status_code == 403


def test_verify_webhook_wrong_mode(client: TestClient):
    resp = client.get(
        "/webhook",
        params={
            "hub.mode": "unsubscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "31415",
        },
    )
    assert resp.status_code == 403


def test_receive_webhook_rejects_missing_signature(
    client: TestClient, audio_payload: dict, inbound_store: AsyncMock
):
    resp = client.post("/webhook", json=audio_payload)

    assert resp.status_code == 401
    inbound_store.record_all.assert_not_called()


def test_receive_webhook_rejects_wrong_signature(
    client: TestClient, audio_payload: dict, inbound_store: AsyncMock
):
    resp = _post_signed(client, audio_payload, secret="not-the-real-secret")

    assert resp.status_code == 401
    inbound_store.record_all.assert_not_called()


def test_receive_webhook_acks_and_dispatches_new_messages(
    client: TestClient,
    handler: AsyncMock,
    inbound_store: AsyncMock,
    audio_payload: dict,
):
    inbound_store.record_all.return_value = [123]

    resp = _post_signed(client, audio_payload)

    # Must ACK 200 immediately...
    assert resp.status_code == 200
    # ...only after durably recording the payload...
    inbound_store.record_all.assert_awaited_once_with(audio_payload)
    # ...and dispatch by the id InboundMessageStore assigned, not the raw payload.
    handler.process_stored_message.assert_awaited_once_with(123)


def test_receive_webhook_skips_dispatch_for_duplicate_delivery(
    client: TestClient, handler: AsyncMock, inbound_store: AsyncMock, text_payload: dict
):
    # A redelivered message: InboundMessageStore recognizes it and returns no new ids.
    inbound_store.record_all.return_value = []

    resp = _post_signed(client, text_payload)

    assert resp.status_code == 200
    handler.process_stored_message.assert_not_awaited()
