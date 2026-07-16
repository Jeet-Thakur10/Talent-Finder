"""make max_experience nullable

Revision ID: 3bf48850f0b7
Revises: 235e3a881606
Create Date: 2026-07-16 12:09:51.487878

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3bf48850f0b7'
down_revision: str | Sequence[str] | None = '235e3a881606'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('job_descriptions', 'max_experience',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('job_descriptions', 'max_experience',
               existing_type=sa.INTEGER(),
               nullable=False)
