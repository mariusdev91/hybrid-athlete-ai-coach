from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str
    full_name: str
    timezone: str = "UTC"


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    timezone: str | None = None


class UserRead(ORMBaseModel):
    id: str
    email: str
    full_name: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class AthleteProfileCreate(BaseModel):
    user_id: str
    birth_date: date | None = None
    age_years: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    height_cm: int | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, gt=20, le=400)
    primary_sport: str | None = None
    sport_position: str | None = None
    season_phase: str | None = None
    weekly_competitions: int | None = Field(default=None, ge=0, le=7)
    experience_level: str | None = None
    training_days_per_week: int | None = None
    session_duration_minutes: int | None = None
    equipment_access: list[str] = Field(default_factory=list)
    performance_priorities: list[str] = Field(default_factory=list)
    limitations_notes: str | None = None


class AthleteProfileUpsert(BaseModel):
    birth_date: date | None = None
    age_years: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    height_cm: int | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, gt=20, le=400)
    primary_sport: str | None = None
    sport_position: str | None = None
    season_phase: str | None = None
    weekly_competitions: int | None = Field(default=None, ge=0, le=7)
    experience_level: str | None = None
    training_days_per_week: int | None = None
    session_duration_minutes: int | None = None
    equipment_access: list[str] | None = None
    performance_priorities: list[str] | None = None
    limitations_notes: str | None = None


class AthleteProfileRead(ORMBaseModel):
    id: str
    user_id: str
    birth_date: date | None = None
    age_years: int | None = None
    gender: str | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    primary_sport: str | None = None
    sport_position: str | None = None
    season_phase: str | None = None
    weekly_competitions: int | None = None
    experience_level: str | None = None
    training_days_per_week: int | None = None
    session_duration_minutes: int | None = None
    equipment_access: list[str]
    performance_priorities: list[str]
    limitations_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class GoalCreate(BaseModel):
    user_id: str
    title: str
    goal_type: str
    status: str = "active"
    priority: int = 3
    target_date: date | None = None
    notes: str | None = None


class GoalRead(ORMBaseModel):
    id: str
    user_id: str
    title: str
    goal_type: str
    status: str
    priority: int
    target_date: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkoutPlanItemInlineCreate(BaseModel):
    week_index: int = Field(default=1, ge=1)
    day_index: int = Field(ge=1)
    sequence_index: int = Field(ge=1)
    session_label: str | None = None
    session_focus: str | None = None
    phase_name: str | None = None
    planned_date: date | None = None
    exercise_id: str | None = None
    exercise_name: str
    prescribed_sets: int | None = Field(default=None, ge=1)
    prescribed_reps: str | None = None
    rest_seconds: int | None = Field(default=None, ge=0)
    target_rpe: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class WorkoutPlanItemCreate(WorkoutPlanItemInlineCreate):
    workout_plan_id: str


class WorkoutPlanItemRead(ORMBaseModel):
    id: str
    workout_plan_id: str
    week_index: int
    day_index: int
    sequence_index: int
    session_label: str | None = None
    session_focus: str | None = None
    phase_name: str | None = None
    planned_date: date | None = None
    exercise_id: str | None = None
    exercise_name: str
    prescribed_sets: int | None = None
    prescribed_reps: str | None = None
    rest_seconds: int | None = None
    target_rpe: int | None = None
    notes: str | None = None


class WorkoutPlanCreate(BaseModel):
    user_id: str
    goal_id: str | None = None
    title: str
    description: str | None = None
    focus: str | None = None
    start_date: date | None = None
    duration_weeks: int | None = None
    sessions_per_week: int | None = None
    status: str = "draft"
    items: list[WorkoutPlanItemInlineCreate] = Field(default_factory=list)


class WorkoutPlanRead(ORMBaseModel):
    id: str
    user_id: str
    goal_id: str | None = None
    title: str
    description: str | None = None
    focus: str | None = None
    start_date: date | None = None
    duration_weeks: int | None = None
    sessions_per_week: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class WorkoutPlanDetailRead(WorkoutPlanRead):
    items: list[WorkoutPlanItemRead] = Field(default_factory=list)


class WorkoutSessionCreate(BaseModel):
    user_id: str
    workout_plan_id: str | None = None
    week_index: int | None = Field(default=None, ge=1)
    day_index: int | None = Field(default=None, ge=1)
    session_label: str | None = None
    title: str | None = None
    status: str = "completed"
    performed_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    perceived_exertion: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class WorkoutSessionRead(ORMBaseModel):
    id: str
    user_id: str
    workout_plan_id: str | None = None
    week_index: int | None = None
    day_index: int | None = None
    session_label: str | None = None
    title: str
    status: str
    performed_at: datetime | None = None
    duration_minutes: int | None = None
    perceived_exertion: int | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
