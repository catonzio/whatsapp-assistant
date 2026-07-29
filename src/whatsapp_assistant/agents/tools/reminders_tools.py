"""Reminders CRUD tools for RemindersAgent (docs/architecture.md §8.4,
requirements.md §4.1).

Scope: CRUD only. Sending reminders proactively (and the budget fallback
that gates it, requirements.md §4.1/§6) is explicitly out of scope here —
see docs/architecture.md §10 point 1 — and will be a separate non-ADK
scheduler that reads the `reminders` table directly.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from whatsapp_assistant.agents.wrappers import may_fail_async
from whatsapp_assistant.database.models.reminder import Reminder, ReminderStatus

logger = logging.getLogger("whatsapp-assistant")


class RemindersRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    @may_fail_async
    async def create_reminder(
        self,
        title: str,
        due_at: str,
        description: str | None = None,
        reminder_timezone: str = "Europe/Rome",
        recurrence_rule: str | None = None,
        linked_item_id: int | None = None,
    ) -> dict:
        """Create a reminder/event.

        Args:
            title: short title of the reminder.
            due_at: ISO-8601 datetime string (e.g. "2026-08-01T09:00:00+02:00")
                of when it's due. Resolve relative dates ("domani", "il 3
                agosto") to an absolute ISO datetime before calling this.
            description: optional longer description.
            reminder_timezone: IANA timezone name, defaults to Europe/Rome.
            recurrence_rule: optional RRULE string (RFC 5545, e.g.
                "FREQ=YEARLY;INTERVAL=1" for a yearly anniversary), or None
                for a one-off reminder.
            linked_item_id: optional id of a catalogued item this reminder
                relates to.

        Returns:
            {"success": True, "reminder_id": int}
        """
        parsed_due_at = datetime.fromisoformat(due_at)
        async with self._sessionmaker() as session:
            reminder = Reminder(
                title=title,
                description=description,
                due_at=parsed_due_at,
                timezone=reminder_timezone,
                recurrence_rule=recurrence_rule,
                linked_item_id=linked_item_id,
            )
            session.add(reminder)
            await session.commit()
            return {"success": True, "reminder_id": reminder.id}

    @may_fail_async
    async def list_reminders(
        self,
        status: str | None = None,
        upcoming_only: bool = True,
    ) -> dict:
        """List reminders, optionally filtered by status.

        Args:
            status: one of "pending", "sent", "done", "cancelled", or None for any.
            upcoming_only: if True (default), only reminders due in the future.

        Returns:
            {"success": True, "reminders": [{"id", "title", "description",
             "due_at", "recurrence_rule", "status"}, ...]}
        """
        async with self._sessionmaker() as session:
            stmt = select(Reminder)
            if status:
                stmt = stmt.where(Reminder.status == ReminderStatus(status))
            if upcoming_only:
                stmt = stmt.where(Reminder.due_at >= datetime.now(timezone.utc))
            rows = (
                (await session.execute(stmt.order_by(Reminder.due_at).limit(50)))
                .scalars()
                .all()
            )

        return {
            "success": True,
            "reminders": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "due_at": r.due_at.isoformat(),
                    "recurrence_rule": r.recurrence_rule,
                    "status": r.status.value,
                }
                for r in rows
            ],
        }

    @may_fail_async
    async def update_reminder(
        self,
        reminder_id: int,
        title: str | None = None,
        due_at: str | None = None,
        description: str | None = None,
        recurrence_rule: str | None = None,
    ) -> dict:
        """Update fields of an existing reminder. Only provided fields change.

        Args:
            reminder_id: id of the reminder to update.
            title: new title, if changing.
            due_at: new ISO-8601 due datetime, if changing.
            description: new description, if changing.
            recurrence_rule: new RRULE string, if changing (pass an empty
                string to clear recurrence).

        Returns:
            {"success": True} or {"success": False, "error": "not_found"}
        """
        async with self._sessionmaker() as session:
            reminder = await session.get(Reminder, reminder_id)
            if reminder is None:
                return {"success": False, "error": "not_found"}
            if title is not None:
                reminder.title = title
            if due_at is not None:
                reminder.due_at = datetime.fromisoformat(due_at)
            if description is not None:
                reminder.description = description
            if recurrence_rule is not None:
                reminder.recurrence_rule = recurrence_rule or None
            await session.commit()
            return {"success": True}

    @may_fail_async
    async def cancel_reminder(self, reminder_id: int) -> dict:
        """Cancel a reminder (marks it as cancelled, does not delete it).

        Args:
            reminder_id: id of the reminder to cancel.

        Returns:
            {"success": True} or {"success": False, "error": "not_found"}
        """
        async with self._sessionmaker() as session:
            reminder = await session.get(Reminder, reminder_id)
            if reminder is None:
                return {"success": False, "error": "not_found"}
            reminder.status = ReminderStatus.CANCELLED
            await session.commit()
            return {"success": True}
