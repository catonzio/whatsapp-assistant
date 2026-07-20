from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from whatsapp_assistant.services.whatsapp.handler import MessageHandler


@pytest.fixture
def whatsapp() -> AsyncMock:
    mock = AsyncMock()
    mock.download_media.return_value = (b"audio-bytes", "audio/ogg")
    return mock


@pytest.fixture
def chat_service() -> AsyncMock:
    mock = AsyncMock()
    mock.send_async.return_value = "risposta dell'agente"
    return mock


@pytest.fixture
def authorized_users() -> AsyncMock:
    mock = AsyncMock()
    mock.is_authorized.return_value = True
    return mock


@pytest.fixture
def inbound_store() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def handler(
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
    authorized_users: AsyncMock,
    inbound_store: AsyncMock,
) -> MessageHandler:
    return MessageHandler(
        whatsapp=whatsapp,
        chat_service=chat_service,
        max_message_len=4096,
        authorized_users=authorized_users,
        inbound_store=inbound_store,
    )


async def test_audio_message_forwarded_as_attachment(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
):
    """Audio is not transcribed — it's forwarded to the agent as a plain
    attachment, exactly like image/video/document."""
    message = {"from": "393331112222", "type": "audio", "audio": {"id": "MEDIA123"}}

    await handler.handle_message(message)

    whatsapp.download_media.assert_awaited_once_with("MEDIA123")
    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.user_id == "393331112222"
    assert sent_message.text == ""
    assert len(sent_message.attachments) == 1
    assert sent_message.attachments[0].mime_type == "audio/ogg"
    whatsapp.send_text.assert_awaited_once_with("393331112222", "risposta dell'agente")


async def test_audio_download_failure_still_forwards_empty_message(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
):
    """A failed download is just a missing attachment, same as for any other
    media type — no special-cased error message for audio."""
    whatsapp.download_media.side_effect = RuntimeError("network down")
    message = {"from": "393331112222", "type": "audio", "audio": {"id": "MEDIA123"}}

    await handler.handle_message(message)

    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.attachments == []


async def test_text_message_goes_to_chat_service(
    handler: MessageHandler, whatsapp: AsyncMock, chat_service: AsyncMock
):
    message = {"from": "393331112222", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.user_id == "393331112222"
    assert sent_message.text == "ciao"
    whatsapp.send_text.assert_awaited_once_with("393331112222", "risposta dell'agente")


async def test_image_message_forwarded_with_caption_and_attachment(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
):
    message = {
        "from": "393331112222",
        "type": "image",
        "image": {"id": "IMG123"},
        "caption": "guarda qui",
    }

    await handler.handle_message(message)

    whatsapp.download_media.assert_awaited_once_with("IMG123")
    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.text == "guarda qui"
    assert len(sent_message.attachments) == 1
    assert sent_message.attachments[0].mime_type == "audio/ogg"  # from the mock


async def test_video_message_forwarded_with_caption_and_attachment(
    handler: MessageHandler, whatsapp: AsyncMock, chat_service: AsyncMock
):
    message = {
        "from": "393331112222",
        "type": "video",
        "video": {"id": "VID123"},
        "caption": "guarda questo video",
    }

    await handler.handle_message(message)

    whatsapp.download_media.assert_awaited_once_with("VID123")
    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.text == "guarda questo video"
    assert len(sent_message.attachments) == 1


async def test_document_message_forwarded_with_caption_and_attachment(
    handler: MessageHandler, whatsapp: AsyncMock, chat_service: AsyncMock
):
    message = {
        "from": "393331112222",
        "type": "document",
        "document": {"id": "DOC123"},
        "caption": "il menu",
    }

    await handler.handle_message(message)

    whatsapp.download_media.assert_awaited_once_with("DOC123")
    sent_message = chat_service.send_async.await_args.args[0]
    assert sent_message.text == "il menu"
    assert len(sent_message.attachments) == 1


async def test_unsupported_message_type_gets_prompt(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
):
    message = {"from": "393331112222", "type": "sticker", "sticker": {"id": "S1"}}

    await handler.handle_message(message)

    chat_service.send_async.assert_not_awaited()
    whatsapp.send_text.assert_awaited_once()
    _, body = whatsapp.send_text.await_args.args
    assert "testo" in body and "vocali" in body


async def test_chat_service_error_sends_fallback(
    handler: MessageHandler, whatsapp: AsyncMock, chat_service: AsyncMock
):
    chat_service.send_async.side_effect = RuntimeError("boom")
    message = {"from": "393331112222", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    _, body = whatsapp.send_text.await_args.args
    assert "qualcosa è andato storto" in body


async def test_long_reply_is_truncated(
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
    authorized_users: AsyncMock,
    inbound_store: AsyncMock,
):
    handler = MessageHandler(
        whatsapp=whatsapp,
        chat_service=chat_service,
        max_message_len=10,
        authorized_users=authorized_users,
        inbound_store=inbound_store,
    )
    chat_service.send_async.return_value = "x" * 100
    message = {"from": "393331112222", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    _, body = whatsapp.send_text.await_args.args
    assert body == "x" * 10


async def test_unauthorized_sender_is_ignored(
    handler: MessageHandler,
    whatsapp: AsyncMock,
    chat_service: AsyncMock,
    authorized_users: AsyncMock,
):
    authorized_users.is_authorized.return_value = False
    message = {"from": "393330009999", "type": "text", "text": {"body": "ciao"}}

    await handler.handle_message(message)

    authorized_users.is_authorized.assert_awaited_once_with("393330009999")
    whatsapp.download_media.assert_not_awaited()
    chat_service.send_async.assert_not_awaited()
    whatsapp.send_text.assert_not_awaited()


async def test_message_without_sender_is_ignored(
    handler: MessageHandler, authorized_users: AsyncMock, chat_service: AsyncMock
):
    await handler.handle_message({"type": "text", "text": {"body": "ciao"}})

    authorized_users.is_authorized.assert_not_awaited()
    chat_service.send_async.assert_not_awaited()


async def test_process_stored_message_marks_done_on_success(
    handler: MessageHandler, inbound_store: AsyncMock, chat_service: AsyncMock
):
    inbound_store.fetch.return_value = SimpleNamespace(
        id=1,
        payload={"from": "393331112222", "type": "text", "text": {"body": "ciao"}},
    )

    await handler.process_stored_message(1)

    inbound_store.mark_processing.assert_awaited_once_with(1)
    chat_service.send_async.assert_awaited_once()
    inbound_store.mark_done.assert_awaited_once_with(1)
    inbound_store.mark_failed.assert_not_awaited()


async def test_process_stored_message_marks_failed_on_unexpected_error(
    handler: MessageHandler, inbound_store: AsyncMock
):
    # Malformed enough to blow up _parse_message itself (type "text" but no
    # "text" key) — a genuinely unrecoverable error, unlike a chat_service
    # failure, which handle_message already recovers from with a user reply.
    inbound_store.fetch.return_value = SimpleNamespace(
        id=2, payload={"from": "393331112222", "type": "text"}
    )

    await handler.process_stored_message(2)

    inbound_store.mark_processing.assert_awaited_once_with(2)
    inbound_store.mark_done.assert_not_awaited()
    inbound_store.mark_failed.assert_awaited_once()
    assert inbound_store.mark_failed.await_args.args[0] == 2


async def test_process_stored_message_skips_vanished_row(
    handler: MessageHandler, inbound_store: AsyncMock, chat_service: AsyncMock
):
    inbound_store.fetch.return_value = None

    await handler.process_stored_message(42)

    inbound_store.mark_processing.assert_not_awaited()
    chat_service.send_async.assert_not_awaited()
