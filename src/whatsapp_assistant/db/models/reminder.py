import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from whatsapp_assistant.db.base import Base


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DONE = "done"
    CANCELLED = "cancelled"


class Reminder(Base):
    """An event/reminder, optionally recurring.

    Recurrence is stored as an RRULE string (RFC 5545 / iCal standard, e.g.
    "FREQ=YEARLY;INTERVAL=1"), parsed at runtime with `dateutil.rrule` to
    compute the next occurrence — the most flexible/standard option, avoids
    inventing a bespoke recurrence format.

    `proactive` marks reminders the bot should send unprompted (subject to
    the monthly budget, see requirements.md §4.1/§6); if the system falls
    back to "on-request only" mode, proactive reminders are simply not
    dispatched automatically anymore, but remain queryable on demand.
    """

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Europe/Rome"
    )
    recurrence_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name="reminder_status"),
        nullable=False,
        default=ReminderStatus.PENDING,
    )
    proactive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    linked_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("items.id"), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
