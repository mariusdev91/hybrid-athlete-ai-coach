"""add basketball profile fields

Revision ID: 20260407_0005
Revises: 20260407_0004
Create Date: 2026-04-07 13:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260407_0005"
down_revision = "20260407_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("athlete_profiles", sa.Column("sport_position", sa.String(length=100), nullable=True))
    op.add_column("athlete_profiles", sa.Column("season_phase", sa.String(length=50), nullable=True))
    op.add_column("athlete_profiles", sa.Column("weekly_competitions", sa.Integer(), nullable=True))
    op.add_column(
        "athlete_profiles",
        sa.Column(
            "performance_priorities",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("athlete_profiles", "performance_priorities")
    op.drop_column("athlete_profiles", "weekly_competitions")
    op.drop_column("athlete_profiles", "season_phase")
    op.drop_column("athlete_profiles", "sport_position")
