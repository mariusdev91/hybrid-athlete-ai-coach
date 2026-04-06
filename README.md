# hybrid-athlete-ai-coach
AI Coach with multi-agent system + RAG + exercise DB.

## Current Scope

The repository is organized around a FastAPI backend plus a lightweight React frontend.
Right now the product supports an MVP flow across both layers:

- athlete creation and editing
- athlete profile persistence and updates
- goal creation and review
- workout plan persistence
- semantic exercise search over a local exercise database
- lightweight AI workout generation and saved plan review

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

The default backend configuration already allows local frontend origins such as
`http://127.0.0.1:4173` and `http://127.0.0.1:5173`. Override
`CORS_ALLOWED_ORIGINS` in `backend/.env` if your frontend runs elsewhere.

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

## Automated Tests

Install dev dependencies and run the smoke tests:

```powershell
python -m pip install -r backend\requirements-dev.txt
Set-Location backend
..\.venv\Scripts\python.exe -m pytest
```

## Frontend Setup

From the repository root:

```powershell
Copy-Item frontend\.env.example frontend\.env
Set-Location frontend
npm install
npm run dev
```

The frontend expects the backend to be running on `http://127.0.0.1:8000` by default. Override `VITE_API_BASE_URL` in `frontend/.env` if needed.

## Useful Endpoints

- `GET /`
- `GET /db/health`
- `GET /exercises/search?q=glutes`
- `GET /test/ai?query=glute workout`
- `GET /admin/vector-store/status`
- `POST /admin/vector-store/rebuild`
- `POST /ai/users/{user_id}/generate-workout`
- `POST /db/users`
- `PATCH /db/users/{user_id}`
- `POST /db/profiles`
- `PUT /db/users/{user_id}/profile`
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

You can also generate a starter workout plan from the saved athlete profile and goal with `POST /ai/users/{user_id}/generate-workout`.

## Notes

- The frontend currently covers the MVP flow in one screen: athlete, profile, goals, exercise search, AI generation, and saved plan review.
- Exercise data is generated from the submodules declared in `.gitmodules`.
- The current priority is product hardening: editable data, stronger flows, and QA polish before deeper feature work.
