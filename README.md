# hybrid-athlete-ai-coach
AI Coach with multi-agent system + RAG + exercise DB.

## Current Scope

The repository is organized around a FastAPI backend plus a lightweight React frontend.
Right now the product supports an MVP flow across both layers:

- athlete creation and editing
- athlete profile persistence and updates
- goal creation and review
- chat-first landing page with guided intake
- plan preview before persistence
- workout plan persistence
- monthly workout plan calendar view on a dedicated page
- session tracking directly from the workout calendar
- Excel export split by training week
- semantic exercise search over a local exercise database
- Bompa-inspired AI workout generation and saved plan review
- sport-specific basketball and football planning modules with season-phase logic

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

The project is now prepared for PostgreSQL-first local development.

Recommended option with Docker:

```powershell
docker compose up -d postgres
```

If you prefer a native PostgreSQL install, create a local database and user that
match `backend/.env.example`, or adjust `DATABASE_URL` in `backend/.env`.

If PostgreSQL is not ready yet, you can temporarily switch back to SQLite by
uncommenting the fallback `DATABASE_URL` in `backend/.env.example` and copying
that into `backend/.env`.

The backend configuration already allows local frontend origins such as
`http://127.0.0.1:4173` and `http://127.0.0.1:5173`. Override
`CORS_ALLOWED_ORIGINS` in `backend/.env` if your frontend runs elsewhere.

Run database migrations:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

If you started PostgreSQL with Docker and want to confirm the container health:

```powershell
docker compose ps
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

The root route `/` now serves a guided chat intake flow that builds a workout preview before persistence. The legacy form-based workspace remains available at `/workspace`.

After confirmation, the saved workout plan opens on a dedicated monthly calendar page, can be logged day by day, and can be downloaded as an Excel workbook with one sheet per week.

For basketball-focused or football-focused workflows, the backend can now use optional profile or AI input fields such as `sport_position`, `season_phase`, `weekly_competitions`, and `performance_priorities` to switch from the generic hybrid plan builder to a sport-specific support module.

## Useful Endpoints

- `GET /`
- `GET /db/health`
- `GET /exercises/search?q=glutes`
- `GET /test/ai?query=glute workout`
- `GET /admin/vector-store/status`
- `POST /admin/vector-store/rebuild`
- `POST /ai/preview-plan`
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
- `GET /db/workout-plans/{workout_plan_id}/sessions`
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

- The frontend currently covers the MVP flow in one screen: athlete, profile, goals, exercise search, AI generation, saved plan review, plus day-by-day session logging on the dedicated plan page.
- The new default frontend flow is chat-first: intake conversation, preview, confirmation, then monthly calendar.
- Local development is now intended to run on PostgreSQL first, with SQLite kept only as a temporary fallback.
- Generated plans now include week-by-week periodization metadata so the UI can render a multi-week calendar and week-based Excel export.
- Generated plans now also include plan start dates and per-session planned dates so the monthly calendar can render the current month accurately.
- The current periodization engine is Bompa-inspired: it progresses through adaptation, accumulation, intensification, and realization phases across the saved plan.
- Basketball and football plans now apply sport-specific templates and season-aware constraints for `off_season`, `pre_season`, `in_season`, and `post_season`.
- Exercise data is generated from the submodules declared in `.gitmodules`.
- The current priority is product hardening: editable data, stronger flows, and QA polish before deeper feature work.
