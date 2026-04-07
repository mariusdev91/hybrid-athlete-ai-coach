from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from datetime import timedelta
from math import ceil
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Goal
from app.db_rel.models import WorkoutPlan
from app.db_rel.models import WorkoutPlanItem
from app.schemas.ai import GeneratedWorkoutPlan
from app.schemas.ai import GeneratedWorkoutPlanItem
from app.schemas.ai import WorkoutGenerationContext
from app.schemas.ai import WorkoutGenerationRequest
from app.services.exercise_lookup import exercise_lookup
from app.services.sport_modules import build_basketball_strategy
from app.services.sport_modules import build_football_strategy
from app.services.sport_modules import is_basketball_context
from app.services.sport_modules import is_football_context
from app.utils.normalizer import normalize_text


BALANCED_DAY_TEMPLATES = [
    {
        "label": "Lower Body Strength",
        "focus": "foundational lower body strength and tissue resilience",
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
        "focus": "upper body strength balance and posture",
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
        "focus": "global work capacity and conditioning tolerance",
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
        "focus": "posterior chain durability and trunk control",
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


GOAL_TRACKS = {
    "mobility": "mobility",
    "recovery": "mobility",
    "conditioning": "endurance",
    "endurance": "endurance",
    "fat loss": "endurance",
    "strength": "strength",
    "performance": "strength",
}


PHASE_LIBRARY = {
    "strength": {
        "Anatomical Adaptation": {
            "headline": "prepare connective tissue, technique, and joint stability",
            "load_note": "higher technical volume, lower intensity",
            "roles": {
                "primary": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 75, "target_rpe": 6},
                "assistance": {"prescribed_sets": 3, "prescribed_reps": "12-15", "rest_seconds": 60, "target_rpe": 6},
                "core": {"prescribed_sets": 2, "prescribed_reps": "12-15", "rest_seconds": 30, "target_rpe": 5},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "40-60 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Accumulation": {
            "headline": "build work capacity and structural strength",
            "load_note": "volume emphasis with progressive overload",
            "roles": {
                "primary": {"prescribed_sets": 4, "prescribed_reps": "8-10", "rest_seconds": 90, "target_rpe": 7},
                "assistance": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 60, "target_rpe": 7},
                "core": {"prescribed_sets": 3, "prescribed_reps": "12-15", "rest_seconds": 30, "target_rpe": 6},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "30-45 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Intensification": {
            "headline": "convert volume into maximal strength emphasis",
            "load_note": "lower reps, longer rest, higher intent",
            "roles": {
                "primary": {"prescribed_sets": 5, "prescribed_reps": "4-6", "rest_seconds": 120, "target_rpe": 8},
                "assistance": {"prescribed_sets": 4, "prescribed_reps": "6-8", "rest_seconds": 75, "target_rpe": 7},
                "core": {"prescribed_sets": 3, "prescribed_reps": "8-12", "rest_seconds": 45, "target_rpe": 6},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "30-45 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Realization": {
            "headline": "reduce fatigue and express the strongest work of the cycle",
            "load_note": "reduced volume with sharp execution",
            "roles": {
                "primary": {"prescribed_sets": 3, "prescribed_reps": "4-5", "rest_seconds": 150, "target_rpe": 7},
                "assistance": {"prescribed_sets": 2, "prescribed_reps": "6-8", "rest_seconds": 75, "target_rpe": 6},
                "core": {"prescribed_sets": 2, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 5},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "30-45 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
    },
    "endurance": {
        "Anatomical Adaptation": {
            "headline": "prepare movement quality and aerobic support work",
            "load_note": "steady volume, lower density",
            "roles": {
                "primary": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 60, "target_rpe": 6},
                "assistance": {"prescribed_sets": 2, "prescribed_reps": "12-15", "rest_seconds": 45, "target_rpe": 6},
                "core": {"prescribed_sets": 2, "prescribed_reps": "12-15", "rest_seconds": 30, "target_rpe": 5},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "40-60 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Accumulation": {
            "headline": "expand work capacity and muscular endurance",
            "load_note": "higher density and repeatability",
            "roles": {
                "primary": {"prescribed_sets": 4, "prescribed_reps": "10-14", "rest_seconds": 60, "target_rpe": 7},
                "assistance": {"prescribed_sets": 3, "prescribed_reps": "12-15", "rest_seconds": 45, "target_rpe": 7},
                "core": {"prescribed_sets": 3, "prescribed_reps": "15-20", "rest_seconds": 30, "target_rpe": 6},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "30-45 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Intensification": {
            "headline": "shift toward specific strength endurance and pace tolerance",
            "load_note": "moderate reps with sharper intent",
            "roles": {
                "primary": {"prescribed_sets": 4, "prescribed_reps": "6-8", "rest_seconds": 75, "target_rpe": 7},
                "assistance": {"prescribed_sets": 3, "prescribed_reps": "8-10", "rest_seconds": 60, "target_rpe": 7},
                "core": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 30, "target_rpe": 6},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "30-45 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Realization": {
            "headline": "freshen up while preserving intensity and movement speed",
            "load_note": "lower volume, maintain quality",
            "roles": {
                "primary": {"prescribed_sets": 3, "prescribed_reps": "6-8", "rest_seconds": 75, "target_rpe": 6},
                "assistance": {"prescribed_sets": 2, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 6},
                "core": {"prescribed_sets": 2, "prescribed_reps": "10-12", "rest_seconds": 30, "target_rpe": 5},
                "mobility": {"prescribed_sets": 2, "prescribed_reps": "30-45 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
    },
    "mobility": {
        "Anatomical Adaptation": {
            "headline": "restore movement quality and tolerance",
            "load_note": "gentle progression and technical control",
            "roles": {
                "primary": {"prescribed_sets": 2, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 5},
                "assistance": {"prescribed_sets": 2, "prescribed_reps": "10-12", "rest_seconds": 45, "target_rpe": 5},
                "core": {"prescribed_sets": 2, "prescribed_reps": "10-12", "rest_seconds": 30, "target_rpe": 5},
                "mobility": {"prescribed_sets": 3, "prescribed_reps": "45-60 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Accumulation": {
            "headline": "build repeatable positions and low-fatigue strength",
            "load_note": "slightly higher volume, control first",
            "roles": {
                "primary": {"prescribed_sets": 3, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 6},
                "assistance": {"prescribed_sets": 3, "prescribed_reps": "10-12", "rest_seconds": 45, "target_rpe": 6},
                "core": {"prescribed_sets": 2, "prescribed_reps": "12-15", "rest_seconds": 30, "target_rpe": 5},
                "mobility": {"prescribed_sets": 3, "prescribed_reps": "45-60 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Intensification": {
            "headline": "translate mobility gains into stronger end-range control",
            "load_note": "moderate effort with strict technique",
            "roles": {
                "primary": {"prescribed_sets": 3, "prescribed_reps": "6-8", "rest_seconds": 60, "target_rpe": 6},
                "assistance": {"prescribed_sets": 2, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 6},
                "core": {"prescribed_sets": 2, "prescribed_reps": "10-12", "rest_seconds": 30, "target_rpe": 5},
                "mobility": {"prescribed_sets": 3, "prescribed_reps": "45-60 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
        "Realization": {
            "headline": "consolidate movement quality and recover fatigue",
            "load_note": "reduced stress, crisp execution",
            "roles": {
                "primary": {"prescribed_sets": 2, "prescribed_reps": "6-8", "rest_seconds": 45, "target_rpe": 5},
                "assistance": {"prescribed_sets": 2, "prescribed_reps": "8-10", "rest_seconds": 45, "target_rpe": 5},
                "core": {"prescribed_sets": 2, "prescribed_reps": "8-10", "rest_seconds": 30, "target_rpe": 4},
                "mobility": {"prescribed_sets": 3, "prescribed_reps": "45-60 sec", "rest_seconds": 30, "target_rpe": None},
            },
        },
    },
}


class WorkoutGeneratorService:
    name = "bompa-inspired-rag-v2"

    def build_context(
        self,
        profile: AthleteProfile | None,
        request: WorkoutGenerationRequest,
    ) -> WorkoutGenerationContext:
        profile_equipment = list(profile.equipment_access) if profile else []
        equipment_access = request.equipment_access or profile_equipment
        profile_priorities = list(profile.performance_priorities) if profile else []
        return WorkoutGenerationContext(
            age_years=profile.age_years if profile else None,
            gender=profile.gender if profile else None,
            height_cm=profile.height_cm if profile else None,
            weight_kg=profile.weight_kg if profile else None,
            primary_sport=profile.primary_sport if profile else None,
            sport_position=request.sport_position or (profile.sport_position if profile else None),
            season_phase=request.season_phase or (profile.season_phase if profile else None),
            weekly_competitions=(
                request.weekly_competitions
                if request.weekly_competitions is not None
                else (profile.weekly_competitions if profile else None)
            ),
            experience_level=profile.experience_level if profile else None,
            equipment_access=equipment_access,
            performance_priorities=request.performance_priorities or profile_priorities,
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
        focus = self._resolve_focus(request, goal, profile)
        start_date = request.start_date or date.today()
        goal_track = self._resolve_goal_track(goal, focus)
        strategy_constraints: list[str] = []
        phase_library = None

        if is_basketball_context(context.primary_sport, focus):
            basketball_strategy = build_basketball_strategy(
                context=context,
                goal=goal,
                focus=focus,
                duration_weeks=request.duration_weeks,
                requested_sessions_per_week=request.sessions_per_week or context.training_days_per_week,
            )
            session_count = basketball_strategy["session_count"]
            title = request.title or basketball_strategy["title"]
            description = request.description or basketball_strategy["description"]
            templates = basketball_strategy["templates"]
            phase_schedule = basketball_strategy["phase_schedule"]
            phase_library = basketball_strategy["phase_library"]
            strategy_constraints = basketball_strategy["constraints"]
            max_slots_per_day = basketball_strategy["max_slots_per_day"]
        elif is_football_context(context.primary_sport, focus):
            football_strategy = build_football_strategy(
                context=context,
                goal=goal,
                focus=focus,
                duration_weeks=request.duration_weeks,
                requested_sessions_per_week=request.sessions_per_week or context.training_days_per_week,
            )
            session_count = football_strategy["session_count"]
            title = request.title or football_strategy["title"]
            description = request.description or football_strategy["description"]
            templates = football_strategy["templates"]
            phase_schedule = football_strategy["phase_schedule"]
            phase_library = football_strategy["phase_library"]
            strategy_constraints = football_strategy["constraints"]
            max_slots_per_day = football_strategy["max_slots_per_day"]
        else:
            session_count = request.sessions_per_week or context.training_days_per_week or 3
            title = request.title or self._build_title(focus, goal)
            description = request.description or self._build_description(focus, goal, context, request.duration_weeks)
            templates = self._resolve_templates(goal, focus, session_count)
            phase_schedule = self._build_phase_schedule(request.duration_weeks, goal_track)
            max_slots_per_day = 3 if context.session_duration_minutes and context.session_duration_minutes < 45 else 4

        day_offsets = self._resolve_training_day_offsets(session_count)
        search_queries: list[str] = []
        items: list[GeneratedWorkoutPlanItem] = []

        for week in phase_schedule:
            for day_index, template in enumerate(templates, start=1):
                used_ids: set[str] = set()
                session_label = template["label"]
                session_focus = self._build_session_focus(template, week)
                planned_date = start_date + timedelta(
                    days=((week["week_index"] - 1) * 7) + day_offsets[day_index - 1]
                )

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

                    prescription = self._build_prescription(
                        slot["role"],
                        week["phase_name"],
                        goal_track=goal_track,
                        phase_library=phase_library,
                    )
                    notes = self._build_item_notes(
                        template,
                        week,
                        context,
                        slot["role"],
                        constraints=strategy_constraints,
                        performance_priorities=context.performance_priorities,
                    )

                    items.append(
                        GeneratedWorkoutPlanItem(
                            week_index=week["week_index"],
                            day_index=day_index,
                            sequence_index=sequence_index,
                            session_label=session_label,
                            session_focus=session_focus,
                            phase_name=week["phase_name"],
                            planned_date=planned_date,
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
            start_date=start_date,
            duration_weeks=request.duration_weeks,
            sessions_per_week=session_count,
            status="draft",
            items=items,
        )
        return plan, context, list(dict.fromkeys(search_queries))

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
            start_date=plan.start_date,
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
                    week_index=item.week_index,
                    day_index=item.day_index,
                    sequence_index=item.sequence_index,
                    session_label=item.session_label,
                    session_focus=item.session_focus,
                    phase_name=item.phase_name,
                    planned_date=item.planned_date,
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

    def _resolve_goal_track(self, goal: Goal | None, focus: str) -> str:
        goal_key = (goal.goal_type if goal else focus).lower()
        for key, track in GOAL_TRACKS.items():
            if key in goal_key:
                return track
        return "strength"

    def _build_title(self, focus: str, goal: Goal | None) -> str:
        if goal:
            return f"{goal.title} - Periodized Plan"
        return f"{focus.title()} - Periodized Plan"

    def _build_description(
        self,
        focus: str,
        goal: Goal | None,
        context: WorkoutGenerationContext,
        duration_weeks: int,
    ) -> str:
        sport = context.primary_sport or "hybrid athlete"
        goal_type = goal.goal_type if goal else "general development"
        return (
            f"Bompa-inspired periodized starter plan for {sport}. "
            f"Focus: {focus}. Goal type: {goal_type}. "
            f"The cycle uses a Bompa-inspired progression across adaptation, accumulation, "
            f"intensification, and realization phases whenever the calendar length allows over {duration_weeks} weeks."
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

    def _resolve_training_day_offsets(self, session_count: int) -> list[int]:
        spacing_map = {
            1: [0],
            2: [0, 3],
            3: [0, 2, 4],
            4: [0, 2, 4, 6],
            5: [0, 1, 3, 5, 6],
            6: [0, 1, 2, 4, 5, 6],
            7: [0, 1, 2, 3, 4, 5, 6],
        }
        return spacing_map.get(session_count, spacing_map[4])

    def _build_phase_schedule(self, duration_weeks: int, goal_track: str) -> list[dict[str, Any]]:
        if duration_weeks <= 1:
            phases = ["Anatomical Adaptation"]
        elif duration_weeks == 2:
            phases = ["Anatomical Adaptation", "Accumulation"]
        elif duration_weeks == 3:
            phases = ["Anatomical Adaptation", "Accumulation", "Realization"]
        elif duration_weeks == 4:
            phases = [
                "Anatomical Adaptation",
                "Accumulation",
                "Intensification",
                "Realization",
            ]
        else:
            adaptation_weeks = 2 if duration_weeks >= 7 else 1
            realization_weeks = 2 if duration_weeks >= 8 else 1
            remaining_weeks = max(0, duration_weeks - adaptation_weeks - realization_weeks)

            if remaining_weeks <= 1:
                accumulation_weeks = remaining_weeks
                intensification_weeks = 0
            else:
                accumulation_weeks = max(1, ceil(remaining_weeks * 0.6))
                intensification_weeks = max(1, remaining_weeks - accumulation_weeks)

                while accumulation_weeks + intensification_weeks > remaining_weeks:
                    accumulation_weeks -= 1

            phases = (
                ["Anatomical Adaptation"] * adaptation_weeks
                + ["Accumulation"] * accumulation_weeks
                + ["Intensification"] * intensification_weeks
                + ["Realization"] * realization_weeks
            )
            phases = phases[:duration_weeks]

        goal_library = PHASE_LIBRARY[goal_track]
        schedule = []
        for week_index, phase_name in enumerate(phases, start=1):
            phase = goal_library[phase_name]
            schedule.append(
                {
                    "week_index": week_index,
                    "phase_name": phase_name,
                    "headline": phase["headline"],
                    "load_note": phase["load_note"],
                }
            )
        return schedule

    def _build_session_focus(self, template: dict[str, Any], week: dict[str, Any]) -> str:
        return f"{week['headline']}; day emphasis: {template['focus']}"

    def _build_item_notes(
        self,
        template: dict[str, Any],
        week: dict[str, Any],
        context: WorkoutGenerationContext,
        role: str,
        constraints: list[str] | None = None,
        performance_priorities: list[str] | None = None,
    ) -> str:
        note_parts = [
            f"{week['phase_name']} block",
            f"Week emphasis: {week['headline']}",
            f"Load strategy: {week['load_note']}",
            f"Session emphasis: {template['focus']}",
        ]
        if performance_priorities:
            note_parts.append(f"Priority qualities: {', '.join(performance_priorities[:3])}")
        if constraints:
            note_parts.extend(constraints[:2])
        if role == "mobility" and context.limitations_notes:
            note_parts.append(f"Respect limitations: {context.limitations_notes}")
        return " | ".join(note_parts)

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

    def _build_prescription(
        self,
        role: str,
        phase_name: str,
        goal_track: str,
        phase_library: dict[str, Any] | None = None,
    ):
        if phase_library is not None:
            return dict(phase_library[phase_name]["roles"][role])
        return dict(PHASE_LIBRARY[goal_track][phase_name]["roles"][role])


workout_generator = WorkoutGeneratorService()
