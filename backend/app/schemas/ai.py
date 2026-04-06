from pydantic import BaseModel
from pydantic import Field

from app.schemas.database import GoalRead
from app.schemas.database import WorkoutPlanDetailRead


class WorkoutGenerationRequest(BaseModel):
    goal_id: str | None = None
    focus: str | None = None
    title: str | None = None
    description: str | None = None
    sessions_per_week: int | None = Field(default=None, ge=1, le=7)
    duration_weeks: int = Field(default=1, ge=1, le=16)
    equipment_access: list[str] | None = None
    limitations_notes: str | None = None
    save_plan: bool = True


class GeneratedWorkoutPlanItem(BaseModel):
    day_index: int
    sequence_index: int
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
    duration_weeks: int
    sessions_per_week: int
    status: str = "draft"
    items: list[GeneratedWorkoutPlanItem] = Field(default_factory=list)


class WorkoutGenerationContext(BaseModel):
    primary_sport: str | None = None
    experience_level: str | None = None
    equipment_access: list[str] = Field(default_factory=list)
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
