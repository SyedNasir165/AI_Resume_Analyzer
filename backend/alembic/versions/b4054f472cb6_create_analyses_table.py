"""create analyses table

Revision ID: b4054f472cb6
Revises: bc6295cc07cf
Create Date: 2026-08-30 08:07:54.894554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b4054f472cb6'
down_revision: Union[str, Sequence[str], None] = 'bc6295cc07cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_type", sa.String(length=32), nullable=False, server_default="general"),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("categories", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("findings", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("observations", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["public.resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["public.profiles.id"], ondelete="CASCADE"),
        schema="public",
    )
    op.create_index("ix_analyses_resume_id", "analyses", ["resume_id"], schema="public")
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"], schema="public")

    op.execute("ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY "Users can manage own analyses"
        ON public.analyses FOR ALL
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_analyses_user_id", table_name="analyses", schema="public")
    op.drop_index("ix_analyses_resume_id", table_name="analyses", schema="public")
    op.drop_table("analyses", schema="public")
