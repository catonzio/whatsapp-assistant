from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from whatsapp_assistant.db.base import Base


class Category(Base):
    """A category of catalogued items (e.g. "ristoranti", "libri", "viaggi").

    Created either explicitly by a user or inferred/invented by the agent.
    No per-category table is ever created: items of any category are stored
    in the generic `items` table, with category-specific fields living in
    `Item.attributes` (JSONB).
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
