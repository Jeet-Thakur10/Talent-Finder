"""add_hiring_manager_notes_to_pipeline

Revision ID: 7b2c3d4e5f6a
Revises: 5a1b2c3d4e5f
Create Date: 2026-07-29 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b2c3d4e5f6a"
down_revision: str | Sequence[str] | None = "5a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "pipeline",
        sa.Column("hiring_manager_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("pipeline", "hiring_manager_notes")
