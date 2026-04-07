from __future__ import annotations

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Goal
from app.schemas.ai import WorkoutGenerationRequest
from app.schemas.ai import WorkoutPlanPreviewGoal
from app.schemas.ai import WorkoutPlanPreviewRequest
from app.schemas.ai import WorkoutPlanPreviewResponse
from app.services.intake_normalization import normalize_goal_type
from app.services.intake_normalization import normalize_primary_sport
from app.services.intake_normalization import normalize_season_phase
from app.services.intake_normalization import sanitize_goal_title
from app.services.workout_generator import workout_generator


def build_preview_response(payload: WorkoutPlanPreviewRequest) -> WorkoutPlanPreviewResponse:
    normalized_primary_sport = normalize_primary_sport(payload.primary_sport) or payload.primary_sport
    normalized_goal_type = normalize_goal_type(payload.goal_type)
    normalized_season_phase = normalize_season_phase(payload.season_phase)
    sanitized_goal_title = sanitize_goal_title(
        payload.goal_title,
        fallback_text=payload.request_text,
        primary_sport=normalized_primary_sport,
        goal_type=normalized_goal_type,
    )

    preview_profile = AthleteProfile(
        user_id="preview-user",
        age_years=payload.age_years,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        primary_sport=normalized_primary_sport,
        sport_position=payload.sport_position,
        season_phase=normalized_season_phase,
        weekly_competitions=payload.weekly_competitions,
        experience_level=payload.experience_level,
        training_days_per_week=payload.training_days_per_week,
        session_duration_minutes=payload.session_duration_minutes,
        equipment_access=payload.equipment_access,
        performance_priorities=payload.performance_priorities,
        limitations_notes=payload.limitations_notes,
    )
    preview_goal = Goal(
        user_id="preview-user",
        title=sanitized_goal_title,
        goal_type=normalized_goal_type,
        priority=1,
        status="active",
    )
    generation_request = WorkoutGenerationRequest(
        goal_id=None,
        focus=None,
        title=None,
        description=None,
        start_date=payload.start_date,
        sessions_per_week=payload.training_days_per_week,
        duration_weeks=payload.duration_weeks,
        sport_position=payload.sport_position,
        season_phase=normalized_season_phase,
        weekly_competitions=payload.weekly_competitions,
        performance_priorities=payload.performance_priorities,
        equipment_access=payload.equipment_access,
        limitations_notes=payload.limitations_notes,
        save_plan=False,
    )
    generated_plan, context, search_queries = workout_generator.generate_plan(
        user_id="preview-user",
        request=generation_request,
        profile=preview_profile,
        goal=preview_goal,
    )

    return WorkoutPlanPreviewResponse(
        generator=workout_generator.name,
        search_queries=search_queries,
        context=context,
        preview_goal=WorkoutPlanPreviewGoal(
            title=preview_goal.title,
            goal_type=preview_goal.goal_type,
        ),
        preview_plan=generated_plan,
    )
