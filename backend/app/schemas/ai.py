from datetime import date
from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from app.schemas.database import ORMBaseModel
from app.schemas.database import GoalRead
from app.schemas.database import UserRead
from app.schemas.database import WorkoutPlanDetailRead


class WorkoutGenerationRequest(BaseModel):
    goal_id: str | None = None
    focus: str | None = None
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    sessions_per_week: int | None = Field(default=None, ge=1, le=7)
    duration_weeks: int = Field(default=1, ge=1, le=16)
    sport_position: str | None = None
    season_phase: str | None = None
    weekly_competitions: int | None = Field(default=None, ge=0, le=7)
    performance_priorities: list[str] | None = None
    equipment_access: list[str] | None = None
    limitations_notes: str | None = None
    save_plan: bool = True


class GeneratedWorkoutPlanItem(BaseModel):
    week_index: int
    day_index: int
    sequence_index: int
    session_label: str | None = None
    session_focus: str | None = None
    phase_name: str | None = None
    planned_date: date | None = None
    exercise_id: str | None = None
    exercise_name: str
    equipment: str | None = None
    primary_muscles: list[str] = Field(default_factory=list)
    secondary_muscles: list[str] = Field(default_factory=list)
    source_query: str
    prescribed_sets: int | None = None
    prescribed_reps: str | None = None
    rest_seconds: int | None = None
    target_rpe: int | None = None
    notes: str | None = None


class GeneratedWorkoutPlan(BaseModel):
    title: str
    description: str | None = None
    focus: str
    start_date: date | None = None
    duration_weeks: int
    sessions_per_week: int
    status: str = "draft"
    items: list[GeneratedWorkoutPlanItem] = Field(default_factory=list)


class WorkoutGenerationContext(BaseModel):
    age_years: int | None = None
    gender: str | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    primary_sport: str | None = None
    sport_position: str | None = None
    season_phase: str | None = None
    weekly_competitions: int | None = None
    experience_level: str | None = None
    equipment_access: list[str] = Field(default_factory=list)
    performance_priorities: list[str] = Field(default_factory=list)
    training_days_per_week: int | None = None
    session_duration_minutes: int | None = None
    limitations_notes: str | None = None


class WorkoutGenerationResponse(BaseModel):
    generator: str
    user_id: str
    goal: GoalRead | None = None
    search_queries: list[str] = Field(default_factory=list)
    context: WorkoutGenerationContext
    generated_plan: GeneratedWorkoutPlan
    saved_workout_plan: WorkoutPlanDetailRead | None = None


class WorkoutPlanPreviewGoal(BaseModel):
    title: str
    goal_type: str


class WorkoutPlanPreviewRequest(BaseModel):
    request_text: str | None = None
    full_name: str | None = None
    age_years: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    height_cm: int | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, gt=20, le=400)
    primary_sport: str
    sport_position: str | None = None
    season_phase: str | None = None
    weekly_competitions: int | None = Field(default=None, ge=0, le=7)
    experience_level: str | None = None
    training_days_per_week: int = Field(default=4, ge=1, le=7)
    session_duration_minutes: int = Field(default=60, ge=15, le=240)
    equipment_access: list[str] = Field(default_factory=list)
    performance_priorities: list[str] = Field(default_factory=list)
    limitations_notes: str | None = None
    goal_title: str
    goal_type: str = "performance"
    duration_weeks: int = Field(default=4, ge=1, le=16)
    start_date: date | None = None
    timezone: str = "UTC"


class WorkoutPlanPreviewResponse(BaseModel):
    generator: str
    search_queries: list[str] = Field(default_factory=list)
    context: WorkoutGenerationContext
    preview_goal: WorkoutPlanPreviewGoal
    preview_plan: GeneratedWorkoutPlan


PlanTrack = Literal["sport", "training_mode"]
ConversationStatus = Literal["collecting", "preview_ready", "confirmed"]
ConversationMessageRole = Literal["assistant", "user"]


class ConversationIntakeState(BaseModel):
    plan_track: PlanTrack | None = None
    request_text: str = ""
    full_name: str = ""
    age_years: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    height_cm: int | None = Field(default=None, ge=80, le=260)
    weight_kg: float | None = Field(default=None, gt=20, le=400)
    primary_sport: str = ""
    sport_position: str = ""
    season_phase: str = ""
    weekly_competitions: int | None = Field(default=None, ge=0, le=7)
    experience_level: str = ""
    training_days_per_week: int = Field(default=4, ge=1, le=7)
    session_duration_minutes: int = Field(default=60, ge=15, le=240)
    equipment_access: list[str] = Field(default_factory=list)
    performance_priorities: list[str] = Field(default_factory=list)
    training_mode: str = ""
    goal_title: str = ""
    goal_type: str = "performance"
    limitations_notes: str = ""
    duration_weeks: int = Field(default=4, ge=1, le=16)
    start_date: date | None = None
    timezone: str = "UTC"


class ConversationCreateRequest(BaseModel):
    plan_track: PlanTrack
    timezone: str = "UTC"


class ConversationMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class ConversationMessageRead(ORMBaseModel):
    id: str
    role: ConversationMessageRole
    content: str
    sequence_index: int
    created_at: datetime
    updated_at: datetime


class ConversationRead(ORMBaseModel):
    id: str
    user_id: str | None = None
    confirmed_workout_plan_id: str | None = None
    plan_track: PlanTrack
    status: ConversationStatus
    timezone: str
    current_step_index: int
    current_prompt: str | None = None
    status_message: str
    is_locked: bool
    intake: ConversationIntakeState
    preview: WorkoutPlanPreviewResponse | None = None
    messages: list[ConversationMessageRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationConfirmResponse(BaseModel):
    conversation: ConversationRead
    user: UserRead
    goal: GoalRead
    saved_workout_plan: WorkoutPlanDetailRead
    generated_plan: GeneratedWorkoutPlan
    context: WorkoutGenerationContext
    search_queries: list[str] = Field(default_factory=list)
