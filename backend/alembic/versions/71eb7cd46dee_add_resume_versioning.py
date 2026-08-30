"""add resume versioning

Revision ID: 71eb7cd46dee
Revises: 76ba9326fb49
Create Date: 2026-08-30 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '71eb7cd46dee'
down_revision: Union[str, Sequence[str], None] = '76ba9326fb49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "resumes", sa.Column("parent_resume_id", postgresql.UUID(as_uuid=True), nullable=True), schema="public"
    )
    op.add_column("resumes", sa.Column("version_label", sa.String(), nullable=True), schema="public")
    op.create_index("ix_resumes_parent_resume_id", "resumes", ["parent_resume_id"], schema="public")
    op.create_foreign_key(
        "fk_resumes_parent_resume_id",
        "resumes",
        "resumes",
        ["parent_resume_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_resumes_parent_resume_id", "resumes", schema="public", type_="foreignkey")
    op.drop_index("ix_resumes_parent_resume_id", table_name="resumes", schema="public")
    op.drop_column("resumes", "version_label", schema="public")
    op.drop_column("resumes", "parent_resume_id", schema="public")
