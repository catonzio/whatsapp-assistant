from whatsapp_assistant.agents.tools.reminders_tools import RemindersRepository
from whatsapp_assistant.database.models.reminder import Reminder

from db_utils import make_sqlite_sessionmaker


async def _repo() -> RemindersRepository:
    sessionmaker = await make_sqlite_sessionmaker(Reminder.__table__)
    return RemindersRepository(sessionmaker=sessionmaker)


async def test_create_reminder_parses_iso_due_at():
    repo = await _repo()

    result = await repo.create_reminder(
        title="Anniversario", due_at="2026-08-01T09:00:00+02:00"
    )

    assert result["success"] is True
    listed = await repo.list_reminders(upcoming_only=False)
    assert listed["reminders"][0]["title"] == "Anniversario"


async def test_create_reminder_rejects_non_iso_due_at():
    repo = await _repo()

    result = await repo.create_reminder(title="Anniversario", due_at="domani")

    assert result["success"] is False
    assert "error" in result


async def test_list_reminders_filters_by_status():
    repo = await _repo()
    created = await repo.create_reminder(
        title="Promemoria", due_at="2099-01-01T09:00:00+00:00"
    )
    await repo.cancel_reminder(created["reminder_id"])

    pending = await repo.list_reminders(status="pending", upcoming_only=False)
    cancelled = await repo.list_reminders(status="cancelled", upcoming_only=False)

    assert pending["reminders"] == []
    assert len(cancelled["reminders"]) == 1


async def test_list_reminders_upcoming_only_excludes_past():
    repo = await _repo()
    await repo.create_reminder(title="Passato", due_at="2000-01-01T09:00:00+00:00")
    await repo.create_reminder(title="Futuro", due_at="2099-01-01T09:00:00+00:00")

    result = await repo.list_reminders(upcoming_only=True)

    assert [r["title"] for r in result["reminders"]] == ["Futuro"]


async def test_update_reminder_changes_only_provided_fields():
    repo = await _repo()
    created = await repo.create_reminder(
        title="Promemoria", due_at="2099-01-01T09:00:00+00:00", description="originale"
    )

    result = await repo.update_reminder(created["reminder_id"], title="Nuovo titolo")

    assert result["success"] is True
    listed = await repo.list_reminders(upcoming_only=False)
    reminder = listed["reminders"][0]
    assert reminder["title"] == "Nuovo titolo"


async def test_update_reminder_changes_due_at_description_and_recurrence():
    repo = await _repo()
    created = await repo.create_reminder(
        title="Anniversario", due_at="2026-08-01T09:00:00+00:00"
    )

    result = await repo.update_reminder(
        created["reminder_id"],
        due_at="2027-08-01T09:00:00+00:00",
        description="Nuova descrizione",
        recurrence_rule="FREQ=YEARLY;INTERVAL=1",
    )

    assert result["success"] is True
    listed = await repo.list_reminders(upcoming_only=False)
    reminder = listed["reminders"][0]
    assert reminder["due_at"].startswith("2027-08-01")
    assert reminder["recurrence_rule"] == "FREQ=YEARLY;INTERVAL=1"


async def test_update_reminder_not_found():
    repo = await _repo()

    result = await repo.update_reminder(reminder_id=999, title="x")

    assert result == {"success": False, "error": "not_found"}


async def test_cancel_reminder_sets_status():
    repo = await _repo()
    created = await repo.create_reminder(
        title="Promemoria", due_at="2099-01-01T09:00:00+00:00"
    )

    result = await repo.cancel_reminder(created["reminder_id"])

    assert result == {"success": True}
    listed = await repo.list_reminders(status="cancelled", upcoming_only=False)
    assert len(listed["reminders"]) == 1


async def test_cancel_reminder_not_found():
    repo = await _repo()

    result = await repo.cancel_reminder(reminder_id=999)

    assert result == {"success": False, "error": "not_found"}
