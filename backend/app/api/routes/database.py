from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Goal
from app.db_rel.models import User
from app.db_rel.models import WorkoutPlan
from app.db_rel.session import get_db
from app.schemas.database import AthleteProfileCreate
from app.schemas.database import AthleteProfileRead
from app.schemas.database import GoalCreate
from app.schemas.database import GoalRead
from app.schemas.database import UserCreate
from app.schemas.database import UserRead
from app.schemas.database import WorkoutPlanCreate
from app.schemas.database import WorkoutPlanRead

router = APIRouter()


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


@router.post("/profiles", response_model=AthleteProfileRead, status_code=201)
def create_athlete_profile(payload: AthleteProfileCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

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


@router.get("/profiles/{user_id}", response_model=AthleteProfileRead)
def get_athlete_profile(user_id: str, db: Session = Depends(get_db)):
    profile = db.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


@router.post("/goals", response_model=GoalRead, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    goal = Goal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/goals/{user_id}", response_model=list[GoalRead])
def list_goals_for_user(user_id: str, db: Session = Depends(get_db)):
    return list(db.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())))


@router.post("/workout-plans", response_model=WorkoutPlanRead, status_code=201)
def create_workout_plan(payload: WorkoutPlanCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.goal_id:
        goal = db.get(Goal, payload.goal_id)
        if not goal or goal.user_id != payload.user_id:
            raise HTTPException(status_code=400, detail="Goal does not belong to the user.")

    plan = WorkoutPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/workout-plans/{user_id}", response_model=list[WorkoutPlanRead])
def list_workout_plans_for_user(user_id: str, db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(WorkoutPlan.created_at.desc())
        )
    )
