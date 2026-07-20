"""Startup crash-recovery for inbound WhatsApp messages.

See docs/architecture.md §6.2: once the webhook acks 200, WhatsApp will never
redeliver that message, so if the process dies between the ack and finishing
`process_stored_message`, nothing but this routine will ever pick it back up.
Called once at app startup (main.py's lifespan) — cheap and safe to call even
when there's nothing to recover.
"""

import logging

from .handler import MessageHandler
from .inbound_store import InboundMessageStore

logger = logging.getLogger("whatsapp-assistant")


async def recover_unfinished_messages(
    handler: MessageHandler, inbound_store: InboundMessageStore
) -> None:
    unfinished = await inbound_store.fetch_unfinished()
    if not unfinished:
        return

    logger.warning(
        "Recovering %d inbound message(s) left unfinished by a previous run",
        len(unfinished),
    )
    for row in unfinished:
        await handler.process_stored_message(row.id)
