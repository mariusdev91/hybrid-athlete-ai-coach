# hybrid-athlete-ai-coach
AI Coach with multi-agent system + RAG + exercise DB.

## Current Scope

The repository is organized around a FastAPI backend and a future frontend shell.
Right now the backend is the active product surface:

- athlete profile and goal persistence
- workout plan persistence
- semantic exercise search over a local exercise database
- lightweight agent orchestration for recommendations and mini-workouts

## Branch Workflow

We work with a simple delivery flow:

- `main` for stable, release-ready code
- `develop` for ongoing integration
- `feature/<scope>-<name>` for new functionality
- `bugfix/<scope>-<name>` for non-urgent fixes
- `hotfix/<scope>-<name>` for urgent production fixes

Recommended flow:

1. Branch from `develop`.
2. Keep one clear objective per branch.
3. Verify locally before merging back into `develop`.
4. Promote to `main` only after validation.

## Backend Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

Create the backend environment file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Run database migrations:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Start the API:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API bootstraps the vector store at startup. If the FAISS index is missing, it is rebuilt from `backend/app/db/exercises.json` and then cached under `backend/app/db/vector_store/`.

## Useful Endpoints

- `GET /`
- `GET /db/health`
- `GET /exercises/search?q=glutes`
- `GET /test/ai?query=glute workout`
- `GET /admin/vector-store/status`
- `POST /admin/vector-store/rebuild`
- `POST /db/users`
- `POST /db/profiles`
- `POST /db/goals`
- `POST /db/workout-plans`
- `GET /db/users/{user_id}/profile`
- `GET /db/users/{user_id}/goals`
- `GET /db/users/{user_id}/workout-plans`
- `GET /db/workout-plans/{workout_plan_id}`
- `GET /db/workout-plans/{workout_plan_id}/items`
- `POST /db/workout-sessions`
- `GET /db/users/{user_id}/workout-sessions`

## Minimal Business Flow

The current backend supports this end-to-end flow:

1. Create a user.
2. Create the athlete profile for that user.
3. Add one or more goals.
4. Create a workout plan, optionally with plan items in the same request.
5. Record completed workout sessions linked to the plan.

## Notes

- The frontend is still a stub and is not part of Sprint 1.
- Exercise data is generated from the submodules declared in `.gitmodules`.
- The immediate Sprint 1 goal is a clean, runnable backend foundation.
