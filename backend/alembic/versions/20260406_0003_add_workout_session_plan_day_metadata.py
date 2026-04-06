"""add workout session plan day metadata

Revision ID: 20260406_0003
Revises: 20260406_0002
Create Date: 2026-04-06 20:15:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260406_0003"
down_revision: str | Sequence[str] | None = "20260406_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_existing_columns() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns("workout_sessions")}


def upgrade() -> None:
    existing_columns = _get_existing_columns()

    if "week_index" not in existing_columns:
        op.add_column("workout_sessions", sa.Column("week_index", sa.Integer(), nullable=True))
    if "day_index" not in existing_columns:
        op.add_column("workout_sessions", sa.Column("day_index", sa.Integer(), nullable=True))
    if "session_label" not in existing_columns:
        op.add_column("workout_sessions", sa.Column("session_label", sa.String(length=255), nullable=True))


def downgrade() -> None:
    existing_columns = _get_existing_columns()

    if "session_label" in existing_columns:
        op.drop_column("workout_sessions", "session_label")
    if "day_index" in existing_columns:
        op.drop_column("workout_sessions", "day_index")
    if "week_index" in existing_columns:
        op.drop_column("workout_sessions", "week_index")
