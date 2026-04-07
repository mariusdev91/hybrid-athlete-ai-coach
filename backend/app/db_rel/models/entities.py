from __future__ import annotations

from datetime import date
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db_rel.base import Base


def generate_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)

    athlete_profile: Mapped["AthleteProfile | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workout_sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AthleteProfile(TimestampMixin, Base):
    __tablename__ = "athlete_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    age_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_sport: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    training_days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipment_access: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    limitations_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="athlete_profile")


class Goal(TimestampMixin, Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="goals")
    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(back_populates="goal")


class WorkoutPlan(TimestampMixin, Base):
    __tablename__ = "workout_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    focus: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    duration_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sessions_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    user: Mapped["User"] = relationship(back_populates="workout_plans")
    goal: Mapped["Goal | None"] = relationship(back_populates="workout_plans")
    items: Mapped[list["WorkoutPlanItem"]] = relationship(
        back_populates="workout_plan",
        cascade="all, delete-orphan",
        order_by=lambda: (
            WorkoutPlanItem.week_index.asc(),
            WorkoutPlanItem.day_index.asc(),
            WorkoutPlanItem.sequence_index.asc(),
        ),
    )
    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="workout_plan")


class WorkoutPlanItem(Base):
    __tablename__ = "workout_plan_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    workout_plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    session_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_focus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phase_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exercise_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    exercise_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prescribed_sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prescribed_reps: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    workout_plan: Mapped["WorkoutPlan"] = relationship(back_populates="items")


class WorkoutSession(TimestampMixin, Base):
    __tablename__ = "workout_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_plan_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workout_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    week_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    perceived_exertion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    workout_plan: Mapped["WorkoutPlan | None"] = relationship(back_populates="sessions")
