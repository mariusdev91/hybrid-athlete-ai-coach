from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Goal
from app.db_rel.models import User
from app.db_rel.models import WorkoutPlan
from app.db_rel.models import WorkoutPlanItem
from app.db_rel.models import WorkoutSession
from app.db_rel.session import get_db
from app.schemas.database import AthleteProfileCreate
from app.schemas.database import AthleteProfileRead
from app.schemas.database import GoalCreate
from app.schemas.database import GoalRead
from app.schemas.database import UserCreate
from app.schemas.database import UserRead
from app.schemas.database import WorkoutPlanCreate
from app.schemas.database import WorkoutPlanDetailRead
from app.schemas.database import WorkoutPlanItemCreate
from app.schemas.database import WorkoutPlanItemRead
from app.schemas.database import WorkoutPlanRead
from app.schemas.database import WorkoutSessionCreate
from app.schemas.database import WorkoutSessionRead

router = APIRouter()


def get_user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def get_goal_or_404(db: Session, goal_id: str) -> Goal:
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return goal


def get_workout_plan_or_404(db: Session, workout_plan_id: str) -> WorkoutPlan:
    plan = db.scalar(
        select(WorkoutPlan)
        .options(selectinload(WorkoutPlan.items))
        .where(WorkoutPlan.id == workout_plan_id)
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Workout plan not found.")
    return plan


def validate_goal_belongs_to_user(db: Session, goal_id: str, user_id: str) -> Goal:
    goal = get_goal_or_404(db, goal_id)
    if goal.user_id != user_id:
        raise HTTPException(status_code=400, detail="Goal does not belong to the user.")
    return goal


def validate_workout_plan_belongs_to_user(db: Session, workout_plan_id: str, user_id: str) -> WorkoutPlan:
    plan = get_workout_plan_or_404(db, workout_plan_id)
    if plan.user_id != user_id:
        raise HTTPException(status_code=400, detail="Workout plan does not belong to the user.")
    return plan


@router.get("/health")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists.")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        timezone=payload.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return get_user_or_404(db, user_id)


@router.post("/profiles", response_model=AthleteProfileRead, status_code=201)
def create_athlete_profile(payload: AthleteProfileCreate, db: Session = Depends(get_db)):
    get_user_or_404(db, payload.user_id)

    existing = db.scalar(
        select(AthleteProfile).where(AthleteProfile.user_id == payload.user_id)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists for this user.")

    profile = AthleteProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/users/{user_id}/profile", response_model=AthleteProfileRead)
def get_athlete_profile(user_id: str, db: Session = Depends(get_db)):
    profile = db.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


@router.post("/goals", response_model=GoalRead, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    get_user_or_404(db, payload.user_id)

    goal = Goal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/users/{user_id}/goals", response_model=list[GoalRead])
def list_goals_for_user(user_id: str, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    return list(db.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())))


@router.post("/workout-plans", response_model=WorkoutPlanRead, status_code=201)
def create_workout_plan(payload: WorkoutPlanCreate, db: Session = Depends(get_db)):
    get_user_or_404(db, payload.user_id)

    if payload.goal_id:
        validate_goal_belongs_to_user(db, payload.goal_id, payload.user_id)

    payload_data = payload.model_dump()
    items_payload = payload_data.pop("items", [])

    plan = WorkoutPlan(**payload_data)
    db.add(plan)
    db.flush()

    for item_payload in items_payload:
        db.add(
            WorkoutPlanItem(
                workout_plan_id=plan.id,
                **item_payload,
            )
        )

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/users/{user_id}/workout-plans", response_model=list[WorkoutPlanRead])
def list_workout_plans_for_user(user_id: str, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    return list(
        db.scalars(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(WorkoutPlan.created_at.desc())
        )
    )


@router.get("/workout-plans/{workout_plan_id}", response_model=WorkoutPlanDetailRead)
def get_workout_plan(workout_plan_id: str, db: Session = Depends(get_db)):
    return get_workout_plan_or_404(db, workout_plan_id)


@router.post("/workout-plan-items", response_model=WorkoutPlanItemRead, status_code=201)
def create_workout_plan_item(payload: WorkoutPlanItemCreate, db: Session = Depends(get_db)):
    get_workout_plan_or_404(db, payload.workout_plan_id)

    item = WorkoutPlanItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/workout-plans/{workout_plan_id}/items", response_model=list[WorkoutPlanItemRead])
def list_workout_plan_items(workout_plan_id: str, db: Session = Depends(get_db)):
    get_workout_plan_or_404(db, workout_plan_id)
    return list(
        db.scalars(
            select(WorkoutPlanItem)
            .where(WorkoutPlanItem.workout_plan_id == workout_plan_id)
            .order_by(WorkoutPlanItem.day_index.asc(), WorkoutPlanItem.sequence_index.asc())
        )
    )


@router.post("/workout-sessions", response_model=WorkoutSessionRead, status_code=201)
def create_workout_session(payload: WorkoutSessionCreate, db: Session = Depends(get_db)):
    get_user_or_404(db, payload.user_id)

    if payload.workout_plan_id:
        validate_workout_plan_belongs_to_user(db, payload.workout_plan_id, payload.user_id)

    session = WorkoutSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/users/{user_id}/workout-sessions", response_model=list[WorkoutSessionRead])
def list_workout_sessions_for_user(user_id: str, db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    return list(
        db.scalars(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user_id)
            .order_by(WorkoutSession.performed_at.desc(), WorkoutSession.created_at.desc())
        )
    )


@router.get("/workout-sessions/{workout_session_id}", response_model=WorkoutSessionRead)
def get_workout_session(workout_session_id: str, db: Session = Depends(get_db)):
    session = db.get(WorkoutSession, workout_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Workout session not found.")
    return session
