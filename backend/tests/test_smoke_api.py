def create_user(client, email="smoke@example.com"):
    response = client.post(
        "/db/users",
        json={
            "email": email,
            "full_name": "Smoke Test User",
            "timezone": "Europe/Bucharest",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_profile(client, user_id):
    response = client.post(
        "/db/profiles",
        json={
            "user_id": user_id,
            "primary_sport": "hybrid training",
            "experience_level": "intermediate",
            "training_days_per_week": 4,
            "session_duration_minutes": 50,
            "equipment_access": ["body only", "dumbbell"],
            "limitations_notes": "keep overhead volume moderate",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_goal(client, user_id):
    response = client.post(
        "/db/goals",
        json={
            "user_id": user_id,
            "title": "Improve performance and conditioning",
            "goal_type": "performance",
            "priority": 1,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health_and_search_endpoints(client):
    root = client.get("/")
    db_health = client.get("/db/health")
    vector_status = client.get("/admin/vector-store/status")
    search = client.get("/exercises/search", params={"q": "glute bridge", "k": 3})

    assert root.status_code == 200
    assert root.json()["vector_store_ready"] is True
    assert root.json()["exercise_count"] > 0

    assert db_health.status_code == 200
    assert db_health.json() == {"status": "ok"}

    assert vector_status.status_code == 200
    assert vector_status.json()["ready"] is True
    assert vector_status.json()["count"] > 0

    assert search.status_code == 200
    assert search.json()["vector_store_ready"] is True
    assert search.json()["count"] > 0
    assert any("Glute" in item["name"] for item in search.json()["results"])


def test_cors_headers_for_local_frontend(client):
    origin = "http://127.0.0.1:4173"

    preflight = client.options(
        "/db/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    simple = client.get("/db/health", headers={"Origin": origin})

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == origin
    assert simple.status_code == 200
    assert simple.headers["access-control-allow-origin"] == origin


def test_domain_flow_create_and_read(client):
    user = create_user(client, email="domain-flow@example.com")
    user_id = user["id"]

    profile = create_profile(client, user_id)
    goal = create_goal(client, user_id)

    plan = client.post(
        "/db/workout-plans",
        json={
            "user_id": user_id,
            "goal_id": goal["id"],
            "title": "Week 1 Foundation",
            "focus": "strength and conditioning",
            "duration_weeks": 1,
            "sessions_per_week": 4,
            "items": [
                {
                    "day_index": 1,
                    "sequence_index": 1,
                    "exercise_name": "Split Squat with Dumbbells",
                    "prescribed_sets": 4,
                    "prescribed_reps": "8",
                    "rest_seconds": 90,
                    "target_rpe": 7,
                }
            ],
        },
    )
    assert plan.status_code == 201
    plan_id = plan.json()["id"]

    plan_detail = client.get(f"/db/workout-plans/{plan_id}")
    sessions = client.post(
        "/db/workout-sessions",
        json={
            "user_id": user_id,
            "workout_plan_id": plan_id,
            "title": "Day 1 Complete",
            "status": "completed",
            "duration_minutes": 48,
            "perceived_exertion": 7,
        },
    )
    profile_read = client.get(f"/db/users/{user_id}/profile")
    goals_read = client.get(f"/db/users/{user_id}/goals")
    plans_read = client.get(f"/db/users/{user_id}/workout-plans")
    sessions_read = client.get(f"/db/users/{user_id}/workout-sessions")

    assert profile["user_id"] == user_id
    assert goal["user_id"] == user_id

    assert plan_detail.status_code == 200
    assert plan_detail.json()["id"] == plan_id
    assert len(plan_detail.json()["items"]) == 1

    assert sessions.status_code == 201
    assert sessions.json()["workout_plan_id"] == plan_id

    assert profile_read.status_code == 200
    assert goals_read.status_code == 200
    assert len(goals_read.json()) == 1
    assert plans_read.status_code == 200
    assert len(plans_read.json()) == 1
    assert sessions_read.status_code == 200
    assert len(sessions_read.json()) == 1


def test_domain_flow_update_existing_user_and_profile(client):
    user = create_user(client, email="edit-flow@example.com")
    user_id = user["id"]

    created_profile = client.put(
        f"/db/users/{user_id}/profile",
        json={
            "primary_sport": "hybrid training",
            "experience_level": "intermediate",
            "training_days_per_week": 4,
            "session_duration_minutes": 50,
            "equipment_access": ["body only", "dumbbell"],
        },
    )

    updated_user = client.patch(
        f"/db/users/{user_id}",
        json={
            "full_name": "Updated Smoke User",
            "timezone": "UTC",
        },
    )
    updated_profile = client.put(
        f"/db/users/{user_id}/profile",
        json={
            "primary_sport": "strength training",
            "training_days_per_week": 5,
            "equipment_access": ["barbell", "dumbbell"],
        },
    )
    profile_read = client.get(f"/db/users/{user_id}/profile")

    assert created_profile.status_code == 200
    assert created_profile.json()["primary_sport"] == "hybrid training"

    assert updated_user.status_code == 200
    assert updated_user.json()["full_name"] == "Updated Smoke User"
    assert updated_user.json()["timezone"] == "UTC"

    assert updated_profile.status_code == 200
    assert updated_profile.json()["primary_sport"] == "strength training"
    assert updated_profile.json()["training_days_per_week"] == 5
    assert updated_profile.json()["equipment_access"] == ["barbell", "dumbbell"]

    assert profile_read.status_code == 200
    assert profile_read.json()["primary_sport"] == "strength training"


def test_ai_generate_workout_and_save_plan(client):
    user = create_user(client, email="ai-flow@example.com")
    user_id = user["id"]
    create_profile(client, user_id)
    goal = create_goal(client, user_id)

    generated = client.post(
        f"/ai/users/{user_id}/generate-workout",
        json={
            "goal_id": goal["id"],
            "duration_weeks": 2,
            "sessions_per_week": 3,
            "save_plan": True,
        },
    )

    assert generated.status_code == 200
    payload = generated.json()
    assert payload["generator"] == "rule-based-rag-v1"
    assert payload["user_id"] == user_id
    assert payload["goal"]["id"] == goal["id"]
    assert len(payload["search_queries"]) > 0
    assert payload["generated_plan"]["sessions_per_week"] == 3
    assert len(payload["generated_plan"]["items"]) >= 9

    saved_plan = payload["saved_workout_plan"]
    assert saved_plan is not None
    assert saved_plan["user_id"] == user_id
    assert len(saved_plan["items"]) == len(payload["generated_plan"]["items"])

    persisted = client.get(f"/db/workout-plans/{saved_plan['id']}")
    assert persisted.status_code == 200
    assert persisted.json()["id"] == saved_plan["id"]
    assert len(persisted.json()["items"]) == len(saved_plan["items"])
