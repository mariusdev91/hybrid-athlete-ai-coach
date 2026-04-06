from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Goal
from app.db_rel.models import User
from app.db_rel.session import get_db
from app.schemas.ai import WorkoutGenerationRequest
from app.schemas.ai import WorkoutGenerationResponse
from app.schemas.database import GoalRead
from app.schemas.database import WorkoutPlanDetailRead
from app.services.workout_generator import workout_generator


router = APIRouter()


def get_user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def get_profile_for_user(db: Session, user_id: str) -> AthleteProfile | None:
    return db.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))


def get_goal_for_user(
    db: Session,
    user_id: str,
    goal_id: str | None,
) -> Goal | None:
    if goal_id:
        goal = db.get(Goal, goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found.")
        if goal.user_id != user_id:
            raise HTTPException(status_code=400, detail="Goal does not belong to the user.")
        return goal

    return db.scalar(
        select(Goal)
        .where(Goal.user_id == user_id)
        .where(Goal.status == "active")
        .order_by(Goal.priority.asc(), Goal.created_at.desc())
    )


@router.post("/users/{user_id}/generate-workout", response_model=WorkoutGenerationResponse)
def generate_workout_for_user(
    user_id: str,
    payload: WorkoutGenerationRequest,
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)
    profile = get_profile_for_user(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Athlete profile not found. Create the profile before generating a workout.",
        )

    goal = get_goal_for_user(db, user_id, payload.goal_id)
    generated_plan, context, search_queries = workout_generator.generate_plan(
        user_id=user_id,
        request=payload,
        profile=profile,
        goal=goal,
    )

    saved_plan = None
    if payload.save_plan:
        saved_model = workout_generator.save_plan(
            db=db,
            user_id=user_id,
            goal_id=goal.id if goal else None,
            plan=generated_plan,
        )
        saved_plan = WorkoutPlanDetailRead.model_validate(saved_model)

    return WorkoutGenerationResponse(
        generator=workout_generator.name,
        user_id=user_id,
        goal=GoalRead.model_validate(goal) if goal else None,
        search_queries=search_queries,
        context=context,
        generated_plan=generated_plan,
        saved_workout_plan=saved_plan,
    )
