from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from whatsapp_assistant.database.base import Base


class Item(Base):
    """A catalogued item (restaurant, book, movie, trip, song, etc.).

    Common fields (name, notes, rating, location) cover the baseline required
    by requirements.md §4.2. Anything category-specific (e.g. cuisine type for
    a restaurant, author for a book) goes in `attributes`, a free-form JSONB
    bag — the agent's tool decides what to put there, no schema/migration
    needed when a new category or a new attribute shape appears.
    """

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    # Free text location (e.g. city), useful for retrieval like "ristoranti a Roma".
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # `with_variant`: JSONB on Postgres (production, GIN-indexable per
    # docs/architecture.md §4.1), plain JSON on SQLite — same pattern already
    # used for `InboundMessage.payload` to keep this table unit-testable
    # against SQLite without a real Postgres.
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
