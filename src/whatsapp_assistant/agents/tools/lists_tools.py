"""Shopping-list/task tools for ListsTasksAgent (docs/architecture.md §8.5,
requirements.md §4.4).

Shopping lists and shared tasks share the same generic List/ListItem schema,
discriminated by `list_type` — no separate tables/tools per type.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from whatsapp_assistant.agents.wrappers import may_fail_async
from whatsapp_assistant.database.models.list import List, ListItem, ListType

logger = logging.getLogger("whatsapp-assistant")


class ListsRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    @may_fail_async
    async def create_list(self, list_type: str, name: str) -> dict:
        """Create a new shared list.

        Args:
            list_type: "shopping" or "task".
            name: display name for the list (e.g. "Spesa settimanale").

        Returns:
            {"success": True, "list_id": int}
        """
        async with self._sessionmaker() as session:
            new_list = List(list_type=ListType(list_type), name=name)
            session.add(new_list)
            await session.commit()
            return {"success": True, "list_id": new_list.id}

    @may_fail_async
    async def find_lists(self, list_type: str | None = None) -> dict:
        """Find existing shared lists, optionally filtered by type — use
        this before create_list to avoid creating a duplicate list.

        Args:
            list_type: "shopping" or "task", or None for both.

        Returns:
            {"success": True, "lists": [{"id", "list_type", "name"}, ...]}
        """
        async with self._sessionmaker() as session:
            stmt = select(List)
            if list_type:
                stmt = stmt.where(List.list_type == ListType(list_type))
            rows = (await session.execute(stmt)).scalars().all()

        return {
            "success": True,
            "lists": [
                {"id": row.id, "list_type": row.list_type.value, "name": row.name}
                for row in rows
            ],
        }

    @may_fail_async
    async def add_list_item(
        self,
        list_id: int,
        description: str,
        attributes: dict | None = None,
    ) -> dict:
        """Add an entry to a list (a shopping item, or a task).

        Args:
            list_id: id of the target list.
            description: text of the item/task.
            attributes: for tasks, free-form fields like {"priority": "alta",
                "due_date": "2026-08-01", "assigned_to": "..."}.

        Returns:
            {"success": True, "list_item_id": int}
        """
        async with self._sessionmaker() as session:
            item = ListItem(
                list_id=list_id, description=description, attributes=attributes
            )
            session.add(item)
            await session.commit()
            return {"success": True, "list_item_id": item.id}

    @may_fail_async
    async def check_list_item(self, list_item_id: int, checked: bool = True) -> dict:
        """Mark a list entry as checked/done, or uncheck it.

        Args:
            list_item_id: id of the entry to update.
            checked: True to mark as done/checked, False to uncheck.

        Returns:
            {"success": True} or {"success": False, "error": "not_found"}
        """
        async with self._sessionmaker() as session:
            item = await session.get(ListItem, list_item_id)
            if item is None:
                return {"success": False, "error": "not_found"}
            item.is_checked = checked
            item.checked_at = datetime.now(timezone.utc) if checked else None
            await session.commit()
            return {"success": True}

    @may_fail_async
    async def remove_list_item(self, list_item_id: int) -> dict:
        """Permanently remove an entry from a list.

        Args:
            list_item_id: id of the entry to remove.

        Returns:
            {"success": True} or {"success": False, "error": "not_found"}
        """
        async with self._sessionmaker() as session:
            item = await session.get(ListItem, list_item_id)
            if item is None:
                return {"success": False, "error": "not_found"}
            await session.delete(item)
            await session.commit()
            return {"success": True}

    @may_fail_async
    async def list_items(self, list_id: int, include_checked: bool = False) -> dict:
        """Get the entries of a list.

        Args:
            list_id: id of the list to read.
            include_checked: if False (default), only unchecked/pending entries.

        Returns:
            {"success": True, "items": [{"id", "description", "is_checked",
             "attributes"}, ...]}
        """
        async with self._sessionmaker() as session:
            stmt = select(ListItem).where(ListItem.list_id == list_id)
            if not include_checked:
                stmt = stmt.where(ListItem.is_checked.is_(False))
            rows = (await session.execute(stmt)).scalars().all()

        return {
            "success": True,
            "items": [
                {
                    "id": row.id,
                    "description": row.description,
                    "is_checked": row.is_checked,
                    "attributes": row.attributes,
                }
                for row in rows
            ],
        }
