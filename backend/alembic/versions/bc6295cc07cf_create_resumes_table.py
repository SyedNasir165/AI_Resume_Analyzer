"""create resumes table

Revision ID: bc6295cc07cf
Revises: f7fdd630167b
Create Date: 2026-08-29 23:34:05.862301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bc6295cc07cf'
down_revision: Union[str, Sequence[str], None] = 'f7fdd630167b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=True),
        sa.Column("file_type", sa.String(length=16), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("warnings", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_confirmation"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["public.profiles.id"], ondelete="CASCADE"),
        schema="public",
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"], schema="public")

    # Defense-in-depth, same posture as profiles: deny by default, own-rows-only.
    op.execute("ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY "Users can manage own resumes"
        ON public.resumes FOR ALL
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_resumes_user_id", table_name="resumes", schema="public")
    op.drop_table("resumes", schema="public")
