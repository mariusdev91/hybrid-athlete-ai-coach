"""add periodized workout plan item metadata"""

from alembic import context
from alembic import op
import sqlalchemy as sa


revision = "20260406_0002"
down_revision = "20260406_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        existing_columns: set[str] = set()
    else:
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        existing_columns = {
            column["name"] for column in inspector.get_columns("workout_plan_items")
        }

    if "week_index" not in existing_columns:
        op.add_column(
            "workout_plan_items",
            sa.Column("week_index", sa.Integer(), nullable=True, server_default="1"),
        )
    if "session_label" not in existing_columns:
        op.add_column(
            "workout_plan_items",
            sa.Column("session_label", sa.String(length=255), nullable=True),
        )
    if "session_focus" not in existing_columns:
        op.add_column(
            "workout_plan_items",
            sa.Column("session_focus", sa.String(length=255), nullable=True),
        )
    if "phase_name" not in existing_columns:
        op.add_column(
            "workout_plan_items",
            sa.Column("phase_name", sa.String(length=100), nullable=True),
        )

    op.execute("UPDATE workout_plan_items SET week_index = 1 WHERE week_index IS NULL")

    with op.batch_alter_table("workout_plan_items") as batch_op:
        batch_op.alter_column(
            "week_index",
            existing_type=sa.Integer(),
            nullable=False,
            server_default=None,
        )


def downgrade() -> None:
    op.drop_column("workout_plan_items", "phase_name")
    op.drop_column("workout_plan_items", "session_focus")
    op.drop_column("workout_plan_items", "session_label")
    op.drop_column("workout_plan_items", "week_index")
