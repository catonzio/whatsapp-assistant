from types import SimpleNamespace
from unittest.mock import AsyncMock

from whatsapp_assistant.services.whatsapp.recovery import recover_unfinished_messages


async def test_recovers_each_unfinished_message():
    handler = AsyncMock()
    inbound_store = AsyncMock()
    inbound_store.fetch_unfinished.return_value = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
    ]

    await recover_unfinished_messages(handler, inbound_store)

    assert handler.process_stored_message.await_args_list == [
        ((1,),),
        ((2,),),
    ]


async def test_noop_when_nothing_unfinished():
    handler = AsyncMock()
    inbound_store = AsyncMock()
    inbound_store.fetch_unfinished.return_value = []

    await recover_unfinished_messages(handler, inbound_store)

    handler.process_stored_message.assert_not_awaited()
