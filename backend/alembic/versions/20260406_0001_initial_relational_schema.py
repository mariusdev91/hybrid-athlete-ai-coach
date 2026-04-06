"""initial relational schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "athlete_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("primary_sport", sa.String(length=100), nullable=True),
        sa.Column("experience_level", sa.String(length=50), nullable=True),
        sa.Column("training_days_per_week", sa.Integer(), nullable=True),
        sa.Column("session_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("equipment_access", sa.JSON(), nullable=False),
        sa.Column("limitations_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "goals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("goal_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)

    op.create_table(
        "workout_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("focus", sa.String(length=100), nullable=True),
        sa.Column("duration_weeks", sa.Integer(), nullable=True),
        sa.Column("sessions_per_week", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workout_plans_goal_id"), "workout_plans", ["goal_id"], unique=False)
    op.create_index(op.f("ix_workout_plans_user_id"), "workout_plans", ["user_id"], unique=False)

    op.create_table(
        "workout_plan_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workout_plan_id", sa.String(length=36), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.String(length=64), nullable=True),
        sa.Column("exercise_name", sa.String(length=255), nullable=False),
        sa.Column("prescribed_sets", sa.Integer(), nullable=True),
        sa.Column("prescribed_reps", sa.String(length=50), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("target_rpe", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["workout_plan_id"], ["workout_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workout_plan_items_exercise_id"), "workout_plan_items", ["exercise_id"], unique=False)
    op.create_index(op.f("ix_workout_plan_items_workout_plan_id"), "workout_plan_items", ["workout_plan_id"], unique=False)

    op.create_table(
        "workout_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("workout_plan_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("perceived_exertion", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workout_plan_id"], ["workout_plans.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workout_sessions_user_id"), "workout_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_workout_sessions_workout_plan_id"), "workout_sessions", ["workout_plan_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workout_sessions_workout_plan_id"), table_name="workout_sessions")
    op.drop_index(op.f("ix_workout_sessions_user_id"), table_name="workout_sessions")
    op.drop_table("workout_sessions")
    op.drop_index(op.f("ix_workout_plan_items_workout_plan_id"), table_name="workout_plan_items")
    op.drop_index(op.f("ix_workout_plan_items_exercise_id"), table_name="workout_plan_items")
    op.drop_table("workout_plan_items")
    op.drop_index(op.f("ix_workout_plans_user_id"), table_name="workout_plans")
    op.drop_index(op.f("ix_workout_plans_goal_id"), table_name="workout_plans")
    op.drop_table("workout_plans")
    op.drop_index(op.f("ix_goals_user_id"), table_name="goals")
    op.drop_table("goals")
    op.drop_table("athlete_profiles")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
