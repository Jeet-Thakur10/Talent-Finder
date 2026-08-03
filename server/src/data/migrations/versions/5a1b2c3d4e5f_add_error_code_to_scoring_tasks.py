"""add_error_code_to_scoring_tasks

Revision ID: 5a1b2c3d4e5f
Revises: 3bf48850f0b7
Create Date: 2026-07-29 12:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5a1b2c3d4e5f"
down_revision: str | Sequence[str] | None = "3bf48850f0b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "scoring_tasks",
        sa.Column("error_code", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("scoring_tasks", "error_code")
