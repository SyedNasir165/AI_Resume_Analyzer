"""add job fields to analyses

Revision ID: 76ba9326fb49
Revises: b4054f472cb6
Create Date: 2026-08-30 08:35:22.668666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '76ba9326fb49'
down_revision: Union[str, Sequence[str], None] = 'b4054f472cb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("analyses", sa.Column("target_role", sa.String(), nullable=True), schema="public")
    op.add_column(
        "analyses",
        sa.Column("job_details", postgresql.JSONB(), nullable=False, server_default="{}"),
        schema="public",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analyses", "job_details", schema="public")
    op.drop_column("analyses", "target_role", schema="public")
