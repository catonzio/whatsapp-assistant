from unittest.mock import AsyncMock

import pytest

from whatsapp_assistant.services.handler import MessageHandler


@pytest.fixture
def whatsapp() -> AsyncMock:
    mock = AsyncMock()
    mock.download_media.return_value = (b"audio-bytes", "audio/ogg")
    return mock


@pytest.fixture
def transcription() -> AsyncMock:
    mock = AsyncMock()
    mock.transcribe.return_value = "testo trascritto"
    return mock


@pytest.fixture
def chat_service() -> AsyncMock:
    mock = AsyncMock()
    mock.send_async.return_value = "risposta dell'agente"
    return mock


@pytest.fixture
def handler(
    whatsapp: AsyncMock, transcription: AsyncMock, chat_service: AsyncMock
) -> MessageHandler:
    return MessageHandler(
        whatsapp=whatsapp,
        transcription=transcription,
        chat_service=chat_service,
        max_message_len=4096,
    )


async def test_audio_message_transcribed_and_replied(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    transcription: AsyncMock,
    chat_service: AsyncMock,
):
    message = {"from": "393331112222", "type": "audio", "audio": {"id": "MEDIA123"}}

    await handler.handle_message(message)

    whatsapp.download_media.assert_awaited_once_with("MEDIA123")
    transcription.transcribe.assert_awaited_once_with(b"audio-bytes", "audio/ogg")
    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.user_id == "393331112222"
    assert sent_message.text == "testo trascritto"
    whatsapp.send_text.assert_awaited_once_with("393331112222", "risposta dell'agente")


async def test_text_message_goes_to_chat_service(
    handler: MessageHandler, whatsapp: AsyncMock, chat_service: AsyncMock
):
    message = {"from": "393331112222", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.user_id == "393331112222"
    assert sent_message.text == "ciao"
    whatsapp.send_text.assert_awaited_once_with("393331112222", "risposta dell'agente")


async def test_unsupported_message_type_gets_prompt(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    transcription: AsyncMock,
    chat_service: AsyncMock,
):
    message = {"from": "393331112222", "type": "image", "image": {"id": "IMG123"}}

    await handler.handle_message(message)

    transcription.transcribe.assert_not_awaited()
    chat_service.send_async.assert_not_awaited()
    whatsapp.send_text.assert_awaited_once()
    _, body = whatsapp.send_text.await_args.args
    assert "testo" in body and "vocali" in body


async def test_transcription_error_sends_fallback(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    transcription: AsyncMock,
    chat_service: AsyncMock,
):
    transcription.transcribe.side_effect = RuntimeError("boom")
    message = {"from": "393331112222", "type": "audio", "audio": {"id": "MEDIA123"}}

    await handler.handle_message(message)

    chat_service.send_async.assert_not_awaited()
    _, body = whatsapp.send_text.await_args.args
    assert "non sono riuscito" in body


async def test_empty_transcription_gets_placeholder(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    transcription: AsyncMock,
    chat_service: AsyncMock,
):
    transcription.transcribe.return_value = "   "
    message = {"from": "393331112222", "type": "audio", "audio": {"id": "MEDIA123"}}

    await handler.handle_message(message)

    chat_service.send_async.assert_not_awaited()
    _, body = whatsapp.send_text.await_args.args
    assert "non ho rilevato" in body.lower()


async def test_chat_service_error_sends_fallback(
    handler: MessageHandler, whatsapp: AsyncMock, chat_service: AsyncMock
):
    chat_service.send_async.side_effect = RuntimeError("boom")
    message = {"from": "393331112222", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    _, body = whatsapp.send_text.await_args.args
    assert "qualcosa è andato storto" in body


async def test_long_reply_is_truncated(
    whatsapp: AsyncMock, transcription: AsyncMock, chat_service: AsyncMock
):
    handler = MessageHandler(
        whatsapp=whatsapp,
        transcription=transcription,
        chat_service=chat_service,
        max_message_len=10,
    )
    chat_service.send_async.return_value = "x" * 100
    message = {"from": "393331112222", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    _, body = whatsapp.send_text.await_args.args
    assert body == "x" * 10


async def test_process_payload_dispatches_each_message(
    handler: MessageHandler, whatsapp: AsyncMock, audio_payload: dict
):
    await handler.process_payload(audio_payload)

    whatsapp.download_media.assert_awaited_once()
    whatsapp.send_text.assert_awaited_once()


async def test_process_payload_swallows_errors(
    handler: MessageHandler, whatsapp: AsyncMock
):
    whatsapp.send_text.side_effect = RuntimeError("network down")
    # A malformed/failing payload must never raise out of the background task.
    await handler.process_payload(
        {
            "entry": [
                {"changes": [{"value": {"messages": [{"from": "x", "type": "text"}]}}]}
            ]
        }
    )


async def test_process_payload_ignores_status_only_payloads(handler: MessageHandler):
    # Delivery/read receipts have no "messages" key — nothing should happen.
    await handler.process_payload(
        {"entry": [{"changes": [{"value": {"statuses": [{"status": "read"}]}}]}]}
    )
