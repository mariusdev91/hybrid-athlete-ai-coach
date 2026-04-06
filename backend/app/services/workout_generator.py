from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Goal
from app.db_rel.models import WorkoutPlan
from app.db_rel.models import WorkoutPlanItem
from app.services.exercise_lookup import exercise_lookup
from app.schemas.ai import GeneratedWorkoutPlan
from app.schemas.ai import GeneratedWorkoutPlanItem
from app.schemas.ai import WorkoutGenerationContext
from app.schemas.ai import WorkoutGenerationRequest
from app.utils.normalizer import normalize_text


BALANCED_DAY_TEMPLATES = [
    {
        "label": "Lower Body Strength",
        "slots": [
            {
                "role": "primary",
                "queries": [
                    {"query": "goblet squat", "primary_muscles": ["quadriceps"]},
                    {"query": "split squat", "primary_muscles": ["quadriceps"]},
                ],
            },
            {
                "role": "assistance",
                "queries": [
                    {"query": "single leg glute bridge", "primary_muscles": ["glutes"]},
                    {"query": "romanian deadlift", "primary_muscles": ["hamstrings"]},
                ],
            },
            {
                "role": "core",
                "queries": [
                    {"query": "reverse crunch", "primary_muscles": ["abdominals"]},
                    {"query": "plank", "primary_muscles": ["abdominals"]},
                ],
            },
            {
                "role": "mobility",
                "queries": [
                    {"query": "hamstring stretch"},
                    {"query": "hip flexor stretch"},
                ],
            },
        ],
    },
    {
        "label": "Upper Body Push Pull",
        "slots": [
            {
                "role": "primary",
                "queries": [
                    {"query": "pushups", "primary_muscles": ["chest"]},
                ],
            },
            {
                "role": "primary",
                "queries": [
                    {"query": "dumbbell row", "primary_muscles": ["middle back"]},
                    {"query": "row", "primary_muscles": ["middle back"]},
                ],
            },
            {
                "role": "assistance",
                "queries": [
                    {"query": "dumbbell shoulder press", "primary_muscles": ["shoulders"]},
                    {"query": "single dumbbell raise", "primary_muscles": ["shoulders"]},
                ],
            },
            {
                "role": "core",
                "queries": [
                    {"query": "plank", "primary_muscles": ["abdominals"]},
                    {"query": "reverse crunch", "primary_muscles": ["abdominals"]},
                ],
            },
        ],
    },
    {
        "label": "Hybrid Conditioning",
        "slots": [
            {
                "role": "primary",
                "queries": [
                    {"query": "split squat", "primary_muscles": ["quadriceps"]},
                    {"query": "bodyweight squat", "primary_muscles": ["quadriceps"]},
                ],
            },
            {
                "role": "primary",
                "queries": [
                    {"query": "pushups", "primary_muscles": ["chest"]},
                    {"query": "single leg glute bridge", "primary_muscles": ["glutes"]},
                ],
            },
            {
                "role": "core",
                "queries": [
                    {"query": "reverse crunch", "primary_muscles": ["abdominals"]},
                    {"query": "plank", "primary_muscles": ["abdominals"]},
                ],
            },
            {
                "role": "mobility",
                "queries": [
                    {"query": "hip flexor stretch"},
                    {"query": "hamstring stretch"},
                ],
            },
        ],
    },
    {
        "label": "Posterior Chain And Core",
        "slots": [
            {
                "role": "primary",
                "queries": [
                    {"query": "romanian deadlift", "primary_muscles": ["hamstrings"]},
                    {"query": "single leg glute bridge", "primary_muscles": ["glutes"]},
                ],
            },
            {
                "role": "assistance",
                "queries": [
                    {"query": "single leg glute bridge", "primary_muscles": ["glutes"]},
                    {"query": "split squat", "primary_muscles": ["quadriceps"]},
                ],
            },
            {
                "role": "primary",
                "queries": [
                    {"query": "dumbbell row", "primary_muscles": ["middle back"]},
                    {"query": "pushups", "primary_muscles": ["chest"]},
                ],
            },
            {
                "role": "core",
                "queries": [
                    {"query": "plank", "primary_muscles": ["abdominals"]},
                    {"query": "reverse crunch", "primary_muscles": ["abdominals"]},
                ],
            },
        ],
    },
]


GOAL_TEMPLATE_MAP = {
    "mobility": [0, 2],
    "recovery": [0, 2],
    "conditioning": [2, 0, 1],
    "endurance": [2, 0, 3],
    "fat loss": [2, 0, 1],
    "strength": [0, 1, 3],
    "performance": [0, 1, 3, 2],
}


ROLE_PRESETS = {
    "primary": {
        "prescribed_sets": 4,
        "prescribed_reps": "6-8",
        "rest_seconds": 90,
        "target_rpe": 7,
    },
    "assistance": {
        "prescribed_sets": 3,
        "prescribed_reps": "8-12",
        "rest_seconds": 60,
        "target_rpe": 7,
    },
    "core": {
        "prescribed_sets": 3,
        "prescribed_reps": "12-15",
        "rest_seconds": 45,
        "target_rpe": 6,
    },
    "mobility": {
        "prescribed_sets": 2,
        "prescribed_reps": "30-45 sec",
        "rest_seconds": 30,
        "target_rpe": None,
    },
}


GOAL_ROLE_ADJUSTMENTS = {
    "conditioning": {
        "primary": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 60},
        "assistance": {"prescribed_sets": 3, "prescribed_reps": "12-15", "rest_seconds": 45},
        "core": {"prescribed_sets": 3, "prescribed_reps": "15-20", "rest_seconds": 30},
    },
    "endurance": {
        "primary": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 60},
        "assistance": {"prescribed_sets": 3, "prescribed_reps": "12-15", "rest_seconds": 45},
    },
    "mobility": {
        "primary": {"prescribed_sets": 3, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 6},
        "assistance": {"prescribed_sets": 2, "prescribed_reps": "10-12", "rest_seconds": 45, "target_rpe": 6},
        "core": {"prescribed_sets": 2, "prescribed_reps": "10-12", "rest_seconds": 30, "target_rpe": 5},
    },
}


class WorkoutGeneratorService:
    name = "rule-based-rag-v1"

    def build_context(
        self,
        profile: AthleteProfile | None,
        request: WorkoutGenerationRequest,
    ) -> WorkoutGenerationContext:
        profile_equipment = list(profile.equipment_access) if profile else []
        equipment_access = request.equipment_access or profile_equipment
        return WorkoutGenerationContext(
            primary_sport=profile.primary_sport if profile else None,
            experience_level=profile.experience_level if profile else None,
            equipment_access=equipment_access,
            training_days_per_week=profile.training_days_per_week if profile else None,
            session_duration_minutes=profile.session_duration_minutes if profile else None,
            limitations_notes=request.limitations_notes or (profile.limitations_notes if profile else None),
        )

    def generate_plan(
        self,
        user_id: str,
        request: WorkoutGenerationRequest,
        profile: AthleteProfile | None = None,
        goal: Goal | None = None,
    ) -> tuple[GeneratedWorkoutPlan, WorkoutGenerationContext, list[str]]:
        context = self.build_context(profile, request)
        session_count = request.sessions_per_week or context.training_days_per_week or 3
        focus = self._resolve_focus(request, goal, profile)
        title = request.title or self._build_title(focus, goal)
        description = request.description or self._build_description(focus, goal, context)

        templates = self._resolve_templates(goal, focus, session_count)
        used_ids: set[str] = set()
        search_queries: list[str] = []
        items: list[GeneratedWorkoutPlanItem] = []
        max_slots_per_day = 3 if context.session_duration_minutes and context.session_duration_minutes < 45 else 4

        for day_index, template in enumerate(templates, start=1):
            for sequence_index, slot in enumerate(template["slots"][:max_slots_per_day], start=1):
                exercise = self._pick_exercise(
                    slot["queries"],
                    context.equipment_access,
                    used_ids,
                    search_queries,
                )
                if not exercise:
                    continue

                if exercise.get("id"):
                    used_ids.add(exercise["id"])

                prescription = self._build_prescription(slot["role"], goal.goal_type if goal else None)
                notes = f"{template['label']} emphasis"
                if slot["role"] == "mobility" and context.limitations_notes:
                    notes = f"{notes}. Respect limitations: {context.limitations_notes}"

                items.append(
                    GeneratedWorkoutPlanItem(
                        day_index=day_index,
                        sequence_index=sequence_index,
                        exercise_id=exercise.get("id"),
                        exercise_name=exercise["name"],
                        equipment=exercise.get("equipment"),
                        primary_muscles=exercise.get("primary_muscles", []),
                        secondary_muscles=exercise.get("secondary_muscles", []),
                        source_query=exercise["source_query"],
                        prescribed_sets=prescription["prescribed_sets"],
                        prescribed_reps=prescription["prescribed_reps"],
                        rest_seconds=prescription["rest_seconds"],
                        target_rpe=prescription["target_rpe"],
                        notes=notes,
                    )
                )

        plan = GeneratedWorkoutPlan(
            title=title,
            description=description,
            focus=focus,
            duration_weeks=request.duration_weeks,
            sessions_per_week=session_count,
            status="draft",
            items=items,
        )
        return plan, context, search_queries

    def save_plan(
        self,
        db: Session,
        user_id: str,
        goal_id: str | None,
        plan: GeneratedWorkoutPlan,
    ) -> WorkoutPlan:
        workout_plan = WorkoutPlan(
            user_id=user_id,
            goal_id=goal_id,
            title=plan.title,
            description=plan.description,
            focus=plan.focus,
            duration_weeks=plan.duration_weeks,
            sessions_per_week=plan.sessions_per_week,
            status=plan.status,
        )
        db.add(workout_plan)
        db.flush()

        for item in plan.items:
            db.add(
                WorkoutPlanItem(
                    workout_plan_id=workout_plan.id,
                    day_index=item.day_index,
                    sequence_index=item.sequence_index,
                    exercise_id=item.exercise_id,
                    exercise_name=item.exercise_name,
                    prescribed_sets=item.prescribed_sets,
                    prescribed_reps=item.prescribed_reps,
                    rest_seconds=item.rest_seconds,
                    target_rpe=item.target_rpe,
                    notes=item.notes,
                )
            )

        db.commit()
        return db.scalar(
            select(WorkoutPlan)
            .options(selectinload(WorkoutPlan.items))
            .where(WorkoutPlan.id == workout_plan.id)
        )

    def _resolve_focus(
        self,
        request: WorkoutGenerationRequest,
        goal: Goal | None,
        profile: AthleteProfile | None,
    ) -> str:
        if request.focus:
            return request.focus
        if goal:
            return goal.title
        if profile and profile.primary_sport:
            return f"{profile.primary_sport} support"
        return "balanced hybrid training"

    def _build_title(self, focus: str, goal: Goal | None) -> str:
        if goal:
            return f"{goal.title} - Starter Plan"
        return f"{focus.title()} - Starter Plan"

    def _build_description(
        self,
        focus: str,
        goal: Goal | None,
        context: WorkoutGenerationContext,
    ) -> str:
        sport = context.primary_sport or "hybrid athlete"
        goal_type = goal.goal_type if goal else "general development"
        return (
            f"Auto-generated starter plan for {sport}. "
            f"Focus: {focus}. Goal type: {goal_type}."
        )

    def _resolve_templates(self, goal: Goal | None, focus: str, session_count: int) -> list[dict[str, Any]]:
        goal_key = (goal.goal_type if goal else focus).lower()
        template_indexes = None
        for key, indexes in GOAL_TEMPLATE_MAP.items():
            if key in goal_key:
                template_indexes = indexes
                break
        if template_indexes is None:
            template_indexes = [0, 1, 2, 3]

        templates = [BALANCED_DAY_TEMPLATES[index] for index in template_indexes]
        selected = []
        for index in range(session_count):
            selected.append(templates[index % len(templates)])
        return selected

    def _pick_exercise(
        self,
        query_options: Iterable[dict[str, Any]],
        allowed_equipment: list[str],
        used_ids: set[str],
        search_queries: list[str],
    ) -> dict[str, Any] | None:
        normalized_equipment = {item.lower() for item in allowed_equipment}
        candidates = []

        for option in query_options:
            query = option["query"]
            search_queries.append(query)
            results = exercise_lookup.search_exercises(
                query=query,
                primary_muscles=option.get("primary_muscles"),
                secondary_muscles=option.get("secondary_muscles"),
                k=8,
            )

            filtered = []
            for exercise in results:
                if exercise.get("id") in used_ids:
                    continue
                if not self._equipment_allowed(exercise.get("equipment"), normalized_equipment):
                    continue
                filtered.append({**exercise, "source_query": query})

            if filtered:
                candidates.extend(filtered)

        if candidates:
            return max(
                candidates,
                key=lambda exercise: (
                    self._score_exercise_match(exercise, exercise["source_query"]),
                    -float(exercise.get("distance", 999999.0)),
                ),
            ).copy()

        fallback_candidates = []
        for option in query_options:
            query = option["query"]
            results = exercise_lookup.search_exercises(query=query, k=8)
            for exercise in results:
                if exercise.get("id") in used_ids:
                    continue
                if not self._equipment_allowed(exercise.get("equipment"), normalized_equipment):
                    continue
                fallback_candidates.append({**exercise, "source_query": query})
        if fallback_candidates:
            return max(
                fallback_candidates,
                key=lambda exercise: (
                    self._score_exercise_match(exercise, exercise["source_query"]),
                    -float(exercise.get("distance", 999999.0)),
                ),
            ).copy()

        return None

    def _equipment_allowed(self, equipment: str | None, allowed_equipment: set[str]) -> bool:
        if not allowed_equipment:
            return True
        if not equipment:
            return True

        equipment_value = equipment.lower()
        if equipment_value == "body only":
            return True
        return equipment_value in allowed_equipment

    def _score_exercise_match(self, exercise: dict[str, Any], query: str) -> int:
        query_text = normalize_text(query)
        exercise_name = normalize_text(exercise.get("name", ""))
        score = 0

        if query_text and query_text in exercise_name:
            score += 10

        query_tokens = [token for token in query_text.split(" ") if token]
        for token in query_tokens:
            if token in exercise_name:
                score += 2

        equipment = normalize_text(exercise.get("equipment") or "")
        if equipment and equipment in query_text:
            score += 1

        return score

    def _build_prescription(self, role: str, goal_type: str | None):
        prescription = dict(ROLE_PRESETS[role])
        if goal_type:
            goal_key = goal_type.lower()
            for key, adjustments in GOAL_ROLE_ADJUSTMENTS.items():
                if key in goal_key and role in adjustments:
                    prescription.update(adjustments[role])
                    break
        return prescription


workout_generator = WorkoutGeneratorService()
