"""Durability/idempotency layer for inbound WhatsApp messages.

Why this exists (docs/architecture.md §6.2): WhatsApp Cloud API delivery is
at-least-once, and Meta's retry/backoff behavior on a non-200 response isn't
precisely documented — it can't be relied on as the system's only durability
mechanism. So instead of "ack 200, then hope background processing finishes",
every message is durably persisted here (unique on `wa_message_id`) *before*
the webhook responds. A crash after the ack can no longer lose the message
(it's already committed to Postgres and gets replayed at next startup by
`recover_unfinished_messages`).

A redelivered `wa_message_id` (same message arriving again — Meta's delivery
is at-least-once, so this is expected, not exceptional) is handled based on
the existing row's status:

- `RECEIVED`/`PROCESSING`: already in flight (or about to be) — skip, don't
  dispatch a second concurrent run.
- `DONE`: already fully handled and replied to — skip, re-running would send
  a duplicate reply.
- `FAILED`: the previous attempt errored out and nothing will ever retry it
  on its own — treat the redelivery as a free retry: flip it back to
  `RECEIVED` and dispatch it again.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from whatsapp_assistant.database.models.inbound_message import (
    InboundMessage,
    InboundMessageStatus,
)

logger = logging.getLogger("whatsapp-assistant")


class InboundMessageStore:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def record_all(self, payload: dict) -> list[int]:
        """Persist every message in a webhook payload.

        Returns the ids of messages that are genuinely new — the caller
        should dispatch processing only for those, skipping duplicates.
        """
        new_ids: list[int] = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    message_id = await self._record_one(message)
                    if message_id is not None:
                        new_ids.append(message_id)
        return new_ids

    async def _record_one(self, message: dict) -> int | None:
        wa_message_id = message.get("id")
        sender = message.get("from")
        if not wa_message_id or not sender:
            logger.warning("Skipping message without id/from: %s", message)
            return None

        async with self._sessionmaker() as session:
            existing = await session.scalar(
                select(InboundMessage).where(
                    InboundMessage.wa_message_id == wa_message_id
                )
            )

            if existing is not None:
                if existing.status != InboundMessageStatus.FAILED:
                    logger.info(
                        "Duplicate delivery of %s (status=%s), skipping",
                        wa_message_id,
                        existing.status.value,
                    )
                    return None
                return await self._retry_failed(session, existing, message)

            row = InboundMessage(
                wa_message_id=wa_message_id, phone_number=sender, payload=message
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                # Lost a race against a concurrent delivery of the same message.
                await session.rollback()
                logger.info(
                    "Duplicate delivery of %s (race), ignoring", wa_message_id
                )
                return None
            return row.id

    async def _retry_failed(
        self, session: AsyncSession, existing: InboundMessage, message: dict
    ) -> int | None:
        """Flip a previously-FAILED row back to RECEIVED so it gets
        re-dispatched, but only if it's *still* FAILED at commit time — this
        is a compare-and-swap, guarding against two near-simultaneous
        redeliveries of the same failed message both winning the retry and
        getting dispatched concurrently.
        """
        result = await session.execute(
            update(InboundMessage)
            .where(
                InboundMessage.id == existing.id,
                InboundMessage.status == InboundMessageStatus.FAILED,
            )
            .values(
                status=InboundMessageStatus.RECEIVED,
                error=None,
                processed_at=None,
                payload=message,
            )
        )
        await session.commit()
        if result.rowcount == 0:
            logger.info(
                "Duplicate delivery of %s lost the retry race, skipping",
                existing.wa_message_id,
            )
            return None
        logger.info("Retrying previously failed message %s", existing.wa_message_id)
        return existing.id

    async def fetch(self, message_id: int) -> InboundMessage | None:
        async with self._sessionmaker() as session:
            return await session.get(InboundMessage, message_id)

    async def mark_processing(self, message_id: int) -> None:
        await self._set_status(message_id, InboundMessageStatus.PROCESSING)

    async def mark_done(self, message_id: int) -> None:
        await self._set_status(message_id, InboundMessageStatus.DONE)

    async def mark_failed(self, message_id: int, error: str) -> None:
        await self._set_status(message_id, InboundMessageStatus.FAILED, error=error)

    _TERMINAL_STATUSES = frozenset(
        {InboundMessageStatus.DONE, InboundMessageStatus.FAILED}
    )

    async def _set_status(
        self,
        message_id: int,
        status: InboundMessageStatus,
        error: str | None = None,
    ) -> None:
        async with self._sessionmaker() as session:
            row = await session.get(InboundMessage, message_id)
            if row is None:
                return
            row.status = status
            if status in self._TERMINAL_STATUSES:
                row.processed_at = datetime.now(timezone.utc)
            if error is not None:
                row.error = error
            await session.commit()

    async def fetch_unfinished(self) -> list[InboundMessage]:
        """Rows stuck in RECEIVED/PROCESSING.

        Within one process's lifetime, every recorded row is always driven to
        DONE or FAILED right after being recorded — so at startup, any row
        still in RECEIVED/PROCESSING can only mean a previous process died
        before finishing it. That's exactly what `recover_unfinished_messages`
        re-dispatches.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(InboundMessage).where(
                    InboundMessage.status.in_(
                        [
                            InboundMessageStatus.RECEIVED,
                            InboundMessageStatus.PROCESSING,
                        ]
                    )
                )
            )
            return list(result.scalars().all())
