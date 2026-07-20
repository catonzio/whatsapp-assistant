import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from whatsapp_assistant.database.base import Base


class InboundMessageStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class InboundMessage(Base):
    """Durable receipt log for inbound WhatsApp messages — see
    docs/architecture.md §6.2.

    Recorded *before* the webhook acks 200, so a crash right after the ack
    can never silently drop a message (unlike relying on Meta's own,
    undocumented retry behavior). `wa_message_id` is unique: a redelivered
    message (WhatsApp is at-least-once) is recognized and skipped instead
    of being processed twice.

    Plain `JSON` (not `postgresql.JSONB`) for `payload`: this table is a
    write-once audit/recovery log, never queried by its JSON content, so it
    doesn't need JSONB's indexing/operator advantages — and staying generic
    keeps it testable against SQLite without a real Postgres.
    """

    __tablename__ = "inbound_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    wa_message_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[InboundMessageStatus] = mapped_column(
        Enum(InboundMessageStatus, name="inbound_message_status"),
        nullable=False,
        default=InboundMessageStatus.RECEIVED,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
