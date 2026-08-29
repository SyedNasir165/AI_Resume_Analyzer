"""create profiles table with auth trigger

Revision ID: f7fdd630167b
Revises:
Create Date: 2026-08-29 23:01:06.339290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f7fdd630167b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        schema="public",
    )

    # Defense-in-depth: even though the backend connects with a privileged role and
    # enforces per-user access in application code, every table still gets RLS enabled
    # with a deny-by-default posture, matching the project's "users only access their
    # own data" rule for any other access path (dashboard SQL editor, future direct
    # frontend reads, etc.).
    op.execute("ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY "Users can view own profile"
        ON public.profiles FOR SELECT
        USING (auth.uid() = id);
        """
    )
    op.execute(
        """
        CREATE POLICY "Users can update own profile"
        ON public.profiles FOR UPDATE
        USING (auth.uid() = id);
        """
    )

    # Auto-provision a profile row whenever Supabase Auth creates a new user, so the
    # backend never has to (and never fabricates) profile data itself.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER SET search_path = public
        AS $$
        BEGIN
          INSERT INTO public.profiles (id, email)
          VALUES (NEW.id, NEW.email);
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user();")
    op.drop_table("profiles", schema="public")
