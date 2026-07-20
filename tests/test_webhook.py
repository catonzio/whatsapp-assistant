from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from whatsapp_assistant.configs.settings import get_settings
from whatsapp_assistant.services.dependencies import get_message_handler
from whatsapp_assistant.main import create_app

VERIFY_TOKEN = "test-verify-token"


@pytest.fixture
def handler() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(handler: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        whatsapp_verify_token=VERIFY_TOKEN
    )
    app.dependency_overrides[get_message_handler] = lambda: handler
    return TestClient(app)


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


def test_receive_webhook_acks_and_processes(
    client: TestClient, handler: AsyncMock, audio_payload: dict
):
    resp = client.post("/webhook", json=audio_payload)

    # Must ACK 200 immediately...
    assert resp.status_code == 200
    # ...and the background task must have handed the payload to the handler.
    handler.process_payload.assert_awaited_once_with(audio_payload)
