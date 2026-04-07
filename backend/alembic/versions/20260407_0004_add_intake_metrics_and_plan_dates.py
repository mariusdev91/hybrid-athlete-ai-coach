"""add intake metrics and plan dates

Revision ID: 20260407_0004
Revises: 20260406_0003
Create Date: 2026-04-07 09:45:00
"""

from collections.abc import Sequence

from alembic import context
from alembic import op
import sqlalchemy as sa


revision: str = "20260407_0004"
down_revision: str | Sequence[str] | None = "20260406_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_existing_columns(table_name: str) -> set[str]:
    if context.is_offline_mode():
        return set()
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    profile_columns = _get_existing_columns("athlete_profiles")
    if "age_years" not in profile_columns:
        op.add_column("athlete_profiles", sa.Column("age_years", sa.Integer(), nullable=True))
    if "height_cm" not in profile_columns:
        op.add_column("athlete_profiles", sa.Column("height_cm", sa.Integer(), nullable=True))
    if "weight_kg" not in profile_columns:
        op.add_column("athlete_profiles", sa.Column("weight_kg", sa.Float(), nullable=True))

    plan_columns = _get_existing_columns("workout_plans")
    if "start_date" not in plan_columns:
        op.add_column("workout_plans", sa.Column("start_date", sa.Date(), nullable=True))

    item_columns = _get_existing_columns("workout_plan_items")
    if "planned_date" not in item_columns:
        op.add_column("workout_plan_items", sa.Column("planned_date", sa.Date(), nullable=True))


def downgrade() -> None:
    if context.is_offline_mode():
        item_columns = {"planned_date"}
        plan_columns = {"start_date"}
        profile_columns = {"weight_kg", "height_cm", "age_years"}
    else:
        item_columns = _get_existing_columns("workout_plan_items")
        plan_columns = _get_existing_columns("workout_plans")
        profile_columns = _get_existing_columns("athlete_profiles")

    if "planned_date" in item_columns:
        op.drop_column("workout_plan_items", "planned_date")

    if "start_date" in plan_columns:
        op.drop_column("workout_plans", "start_date")

    if "weight_kg" in profile_columns:
        op.drop_column("athlete_profiles", "weight_kg")
    if "height_cm" in profile_columns:
        op.drop_column("athlete_profiles", "height_cm")
    if "age_years" in profile_columns:
        op.drop_column("athlete_profiles", "age_years")
