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
    gender: str | None = None
    primary_sport: str | None = None
    experience_level: str | None = None
    training_days_per_week: int | None = None
    session_duration_minutes: int | None = None
    equipment_access: list[str] = Field(default_factory=list)
    limitations_notes: str | None = None


class AthleteProfileRead(ORMBaseModel):
    id: str
    user_id: str
    birth_date: date | None = None
    gender: str | None = None
    primary_sport: str | None = None
    experience_level: str | None = None
    training_days_per_week: int | None = None
    session_duration_minutes: int | None = None
    equipment_access: list[str]
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
    day_index: int = Field(ge=1)
    sequence_index: int = Field(ge=1)
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
    day_index: int
    sequence_index: int
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
    title: str
    status: str = "completed"
    performed_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    perceived_exertion: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class WorkoutSessionRead(ORMBaseModel):
    id: str
    user_id: str
    workout_plan_id: str | None = None
    title: str
    status: str
    performed_at: datetime | None = None
    duration_minutes: int | None = None
    perceived_exertion: int | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
