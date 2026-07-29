"""enable pg_trgm and index items.name

Revision ID: 234761436f4d
Revises: c3cd7067a3d2
Create Date: 2026-07-23 00:00:00.000000

Enables fuzzy matching for the cataloging agent's `find_similar_items` tool
(docs/architecture.md §8.3, requirements.md §7.5 — dedup/update handling).
Previously listed as "da abilitare" in docs/architecture.md §4.1.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '234761436f4d'
down_revision: Union[str, Sequence[str], None] = 'c3cd7067a3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_items_name_trgm "
        "ON items USING gin (name gin_trgm_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_items_name_trgm")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
