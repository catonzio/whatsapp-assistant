import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from whatsapp_assistant.database.base import Base


class ListType(str, enum.Enum):
    SHOPPING = "shopping"
    TASK = "task"


class List(Base):
    """A shared list — either a shopping list or a shared task list.

    Both "liste della spesa" and "task condivisi" (requirements.md §4.4) are
    modeled with the same pair of generic tables (List/ListItem) rather than
    dedicated schemas: they're both fundamentally a named collection of
    checkable entries. Type-specific fields (task priority/due date/assignee)
    live in `ListItem.attributes`, same JSONB pattern used for `Item`.
    """

    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_type: Mapped[ListType] = mapped_column(
        Enum(ListType, name="list_type"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class ListItem(Base):
    """A single entry within a List (a shopping item, or a task)."""

    __tablename__ = "list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("lists.id"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # e.g. for tasks: {"priority": "high", "due_date": "...", "assigned_to": <user_id>}
    # `with_variant`: JSONB on Postgres, plain JSON on SQLite — same
    # rationale as Item.attributes.
    attributes: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
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
