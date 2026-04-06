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


class WorkoutPlanCreate(BaseModel):
    user_id: str
    goal_id: str | None = None
    title: str
    description: str | None = None
    focus: str | None = None
    duration_weeks: int | None = None
    sessions_per_week: int | None = None
    status: str = "draft"


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
