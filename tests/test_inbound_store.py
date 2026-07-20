import asyncio

import pytest

from db_utils import make_sqlite_sessionmaker
from whatsapp_assistant.database.models.inbound_message import (
    InboundMessage,
    InboundMessageStatus,
)
from whatsapp_assistant.services.whatsapp.inbound_store import InboundMessageStore


def _message(wa_message_id: str = "wamid.1", sender: str = "393331112222") -> dict:
    return {
        "from": sender,
        "id": wa_message_id,
        "type": "text",
        "text": {"body": "ciao"},
    }


def _payload(*messages: dict) -> dict:
    return {
        "entry": [{"changes": [{"value": {"messages": list(messages)}}]}],
    }


@pytest.fixture
async def store() -> InboundMessageStore:
    sessionmaker = await make_sqlite_sessionmaker(InboundMessage.__table__)
    return InboundMessageStore(sessionmaker)


async def test_record_all_persists_new_messages(store: InboundMessageStore):
    ids = await store.record_all(_payload(_message("wamid.1"), _message("wamid.2")))

    assert len(ids) == 2
    row = await store.fetch(ids[0])
    assert row is not None
    assert row.wa_message_id == "wamid.1"
    assert row.phone_number == "393331112222"
    assert row.status == InboundMessageStatus.RECEIVED
    assert row.payload["id"] == "wamid.1"


async def test_record_all_skips_redelivery_while_received(store: InboundMessageStore):
    first_ids = await store.record_all(_payload(_message("wamid.dup")))
    second_ids = await store.record_all(_payload(_message("wamid.dup")))

    assert len(first_ids) == 1
    assert second_ids == []  # still RECEIVED: already about to be handled.


async def test_record_all_skips_redelivery_while_processing(
    store: InboundMessageStore,
):
    [message_id] = await store.record_all(_payload(_message("wamid.inflight")))
    await store.mark_processing(message_id)

    ids = await store.record_all(_payload(_message("wamid.inflight")))

    assert ids == []  # already being handled right now — don't dispatch twice.
    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.PROCESSING


async def test_record_all_skips_redelivery_while_done(store: InboundMessageStore):
    [message_id] = await store.record_all(_payload(_message("wamid.finished")))
    await store.mark_done(message_id)

    ids = await store.record_all(_payload(_message("wamid.finished")))

    assert ids == []  # already replied to — reprocessing would double-reply.
    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.DONE


async def test_record_all_retries_redelivery_while_failed(store: InboundMessageStore):
    [message_id] = await store.record_all(_payload(_message("wamid.broken")))
    await store.mark_failed(message_id, "boom")

    ids = await store.record_all(_payload(_message("wamid.broken")))

    # A redelivery of a message that previously errored out is treated as a
    # free retry: same row, flipped back to RECEIVED, error cleared.
    assert ids == [message_id]
    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.RECEIVED
    assert row.error is None
    assert row.processed_at is None


async def test_concurrent_redelivery_of_failed_message_retries_only_once(
    store: InboundMessageStore,
):
    [message_id] = await store.record_all(_payload(_message("wamid.race")))
    await store.mark_failed(message_id, "boom")

    results = await asyncio.gather(
        store.record_all(_payload(_message("wamid.race"))),
        store.record_all(_payload(_message("wamid.race"))),
    )

    # Both redeliveries raced to retry the same FAILED row — exactly one
    # must win (the compare-and-swap in _retry_failed), not both.
    non_empty = [ids for ids in results if ids]
    assert non_empty == [[message_id]]


async def test_retry_failed_is_a_noop_if_row_no_longer_failed(
    store: InboundMessageStore,
):
    """Deterministic version of the race above: force the row to change
    status *between* the initial read and the compare-and-swap update,
    directly exercising the "lost the race" branch instead of relying on
    asyncio scheduling luck to hit it."""
    [message_id] = await store.record_all(_payload(_message("wamid.cas")))
    await store.mark_failed(message_id, "boom")

    async with store._sessionmaker() as session:
        existing = await session.get(InboundMessage, message_id)
        await store.mark_done(message_id)  # someone else got there first
        result = await store._retry_failed(session, existing, _message("wamid.cas"))

    assert result is None
    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.DONE  # untouched by the loser


async def test_concurrent_first_delivery_creates_only_one_row(
    store: InboundMessageStore,
):
    results = await asyncio.gather(
        store.record_all(_payload(_message("wamid.newrace"))),
        store.record_all(_payload(_message("wamid.newrace"))),
    )

    non_empty = [ids for ids in results if ids]
    assert len(non_empty) == 1


async def test_record_all_skips_message_without_id_or_sender(store: InboundMessageStore):
    malformed = {"type": "text", "text": {"body": "no id or sender"}}
    ids = await store.record_all(_payload(malformed))

    assert ids == []


async def test_mark_processing_then_done(store: InboundMessageStore):
    [message_id] = await store.record_all(_payload(_message("wamid.3")))

    await store.mark_processing(message_id)
    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.PROCESSING
    assert row.processed_at is None

    await store.mark_done(message_id)
    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.DONE
    assert row.processed_at is not None


async def test_mark_failed_records_error(store: InboundMessageStore):
    [message_id] = await store.record_all(_payload(_message("wamid.4")))

    await store.mark_failed(message_id, "boom")

    row = await store.fetch(message_id)
    assert row.status == InboundMessageStatus.FAILED
    assert row.error == "boom"


async def test_mark_status_on_missing_row_is_a_noop(store: InboundMessageStore):
    # Should not raise even though no row with this id exists.
    await store.mark_done(999999)


async def test_fetch_unfinished_returns_only_received_and_processing(
    store: InboundMessageStore,
):
    [received_id] = await store.record_all(_payload(_message("wamid.received")))
    [processing_id] = await store.record_all(_payload(_message("wamid.processing")))
    [done_id] = await store.record_all(_payload(_message("wamid.done")))
    [failed_id] = await store.record_all(_payload(_message("wamid.failed")))

    await store.mark_processing(processing_id)
    await store.mark_done(done_id)
    await store.mark_failed(failed_id, "boom")

    unfinished = await store.fetch_unfinished()
    unfinished_ids = {row.id for row in unfinished}

    assert unfinished_ids == {received_id, processing_id}
