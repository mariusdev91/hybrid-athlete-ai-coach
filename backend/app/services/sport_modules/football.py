from __future__ import annotations

from math import ceil
from typing import Any

from app.utils.normalizer import normalize_text


FOOTBALL_KEYWORDS = (
    "football",
    "soccer",
    "striker",
    "winger",
    "midfielder",
    "defender",
    "fullback",
    "full back",
    "center back",
    "goalkeeper",
    "keeper",
    "gk",
)

SEASON_PHASE_ALIASES = {
    "offseason": "off_season",
    "off season": "off_season",
    "off_season": "off_season",
    "general preparation": "off_season",
    "preseason": "pre_season",
    "pre season": "pre_season",
    "pre_season": "pre_season",
    "specific preparation": "pre_season",
    "inseason": "in_season",
    "in season": "in_season",
    "in_season": "in_season",
    "competition": "in_season",
    "competitive": "in_season",
    "postseason": "post_season",
    "post season": "post_season",
    "post_season": "post_season",
    "transition": "post_season",
    "restoration": "post_season",
}

PRIORITY_TAG_MAP = {
    "acceleration": ("acceleration", "speed"),
    "first step": ("acceleration", "speed"),
    "top speed": ("max_speed", "speed"),
    "max speed": ("max_speed", "speed"),
    "speed": ("max_speed", "speed"),
    "change of direction": ("change_of_direction", "speed"),
    "cod": ("change_of_direction", "speed"),
    "agility": ("change_of_direction", "speed"),
    "repeat sprint": ("repeat_sprint", "conditioning"),
    "conditioning": ("repeat_sprint", "conditioning"),
    "hamstring": ("hamstring_resilience", "resilience"),
    "adductor": ("adductor_resilience", "resilience"),
    "groin": ("adductor_resilience", "resilience"),
    "aerial": ("aerial_power", "elastic"),
}

DEFAULT_PRIORITIES = [
    "acceleration",
    "repeat sprint",
    "hamstring resilience",
]

SEASON_CONFIG = {
    "off_season": {"default_sessions": 4, "max_sessions": 5},
    "pre_season": {"default_sessions": 4, "max_sessions": 5},
    "in_season": {"default_sessions": 3, "max_sessions": 4},
    "post_season": {"default_sessions": 3, "max_sessions": 3},
}


def slot(role: str, *queries: tuple[str, str | None]):
    payload = []
    for query, primary in queries:
        item: dict[str, Any] = {"query": query}
        if primary:
            item["primary_muscles"] = [primary]
        payload.append(item)
    return {"role": role, "queries": payload}


def rx(sets: int, reps: str, rest: int, rpe: int | None):
    return {
        "prescribed_sets": sets,
        "prescribed_reps": reps,
        "rest_seconds": rest,
        "target_rpe": rpe,
    }


def role_block(
    force,
    upper_strength,
    assistance,
    elastic,
    speed,
    conditioning,
    core,
    mobility,
):
    return {
        "force": force,
        "upper_strength": upper_strength,
        "assistance": assistance,
        "elastic": elastic,
        "speed": speed,
        "conditioning": conditioning,
        "core": core,
        "mobility": mobility,
    }


FOOTBALL_TEMPLATE_LIBRARY = {
    "off_season": [
        {
            "label": "Acceleration And Hamstring Force",
            "focus": "first-step force, hamstring robustness, and sprint mechanics",
            "tags": ["acceleration", "hamstring_resilience", "speed"],
            "slots": [
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("wind sprints", "abdominals")),
                slot("force", ("bodyweight walking lunge", "quadriceps"), ("split squat with dumbbells", "quadriceps"), ("goblet squat", "quadriceps")),
                slot("assistance", ("single leg glute bridge", "glutes"), ("platform hamstring slides", "hamstrings"), ("hamstring stretch", "hamstrings")),
                slot("core", ("plank", "abdominals"), ("reverse crunch", "abdominals")),
                slot("mobility", ("seated floor hamstring stretch", None), ("standing hamstring and calf stretch", None)),
            ],
        },
        {
            "label": "Max Velocity And Calf Stiffness",
            "focus": "top-speed support, calf stiffness, and elastic lower-leg work",
            "tags": ["max_speed", "repeat_sprint", "resilience"],
            "slots": [
                slot("speed", ("wind sprints", "abdominals"), ("single-cone sprint drill", "quadriceps")),
                slot("elastic", ("front box jump", "hamstrings"), ("freehand jump squat", "quadriceps"), ("lateral box jump", "adductors")),
                slot("assistance", ("standing dumbbell calf raise", "calves"), ("calf raise on a dumbbell", "calves"), ("single leg glute bridge", "glutes")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
            ],
        },
        {
            "label": "COD And Adductor Control",
            "focus": "change of direction, deceleration control, and groin tolerance",
            "tags": ["change_of_direction", "adductor_resilience", "force"],
            "slots": [
                slot("speed", ("side hop-sprint", "quadriceps"), ("single-cone sprint drill", "quadriceps")),
                slot("force", ("crossover reverse lunge", "quadriceps"), ("bodyweight walking lunge", "quadriceps"), ("split squats", "quadriceps")),
                slot("assistance", ("adductor/groin", "adductors"), ("groiners", "adductors"), ("side lying groin stretch", "adductors")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
                slot("mobility", ("groin and back stretch", None), ("hamstring stretch", None)),
            ],
        },
        {
            "label": "Repeat Sprint And Aerobic Power",
            "focus": "repeat sprint ability and match-like work capacity",
            "tags": ["repeat_sprint", "conditioning", "acceleration"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps"), ("single-cone sprint drill", "quadriceps")),
                slot("speed", ("side hop-sprint", "quadriceps"), ("wind sprints", "abdominals")),
                slot("force", ("bodyweight walking lunge", "quadriceps"), ("single leg glute bridge", "glutes")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
                slot("mobility", ("hamstring stretch", None), ("adductor/groin", "adductors")),
            ],
        },
    ],
    "pre_season": [
        {
            "label": "Match Speed Integration",
            "focus": "blend sprint qualities, elastic work, and football readiness",
            "tags": ["acceleration", "max_speed", "repeat_sprint"],
            "slots": [
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("wind sprints", "abdominals"), ("side hop-sprint", "quadriceps")),
                slot("elastic", ("front box jump", "hamstrings"), ("freehand jump squat", "quadriceps")),
                slot("force", ("split squat with dumbbells", "quadriceps"), ("bodyweight walking lunge", "quadriceps")),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
            ],
        },
        {
            "label": "Strength Maintenance And Hamstrings",
            "focus": "preserve force production while protecting the posterior chain",
            "tags": ["hamstring_resilience", "force", "resilience"],
            "slots": [
                slot("force", ("split squat with dumbbells", "quadriceps"), ("goblet squat", "quadriceps"), ("bodyweight walking lunge", "quadriceps")),
                slot("assistance", ("single leg glute bridge", "glutes"), ("platform hamstring slides", "hamstrings"), ("hamstring stretch", "hamstrings")),
                slot("assistance", ("standing dumbbell calf raise", "calves"), ("calf raise on a dumbbell", "calves")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Repeat Sprint Readiness",
            "focus": "prepare for repeated high-intensity efforts with short recoveries",
            "tags": ["repeat_sprint", "conditioning"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps")),
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("side hop-sprint", "quadriceps")),
                slot("mobility", ("hamstring stretch", None), ("adductor/groin", "adductors")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Mobility And Groin Care",
            "focus": "keep hips, groins, and calves ready for competition density",
            "tags": ["mobility", "adductor_resilience", "resilience"],
            "slots": [
                slot("mobility", ("adductor/groin", "adductors"), ("side lying groin stretch", "adductors"), ("groiners", "adductors")),
                slot("assistance", ("single leg glute bridge", "glutes"), ("standing dumbbell calf raise", "calves")),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
            ],
        },
    ],
    "in_season": [
        {
            "label": "Neural Speed Primer",
            "focus": "keep sprint sharpness alive without adding match fatigue",
            "tags": ["acceleration", "max_speed", "speed"],
            "slots": [
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("wind sprints", "abdominals")),
                slot("elastic", ("front box jump", "hamstrings"), ("freehand jump squat", "quadriceps")),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
            ],
        },
        {
            "label": "Strength Maintenance",
            "focus": "micro-dose lower-body force and posterior chain support",
            "tags": ["force", "hamstring_resilience"],
            "slots": [
                slot("force", ("split squat with dumbbells", "quadriceps"), ("bodyweight walking lunge", "quadriceps")),
                slot("assistance", ("single leg glute bridge", "glutes"), ("standing dumbbell calf raise", "calves")),
                slot("assistance", ("hamstring stretch", "hamstrings"), ("adductor/groin", "adductors")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Recovery And Adductors",
            "focus": "restore range of motion and reduce soft-tissue stress between matches",
            "tags": ["mobility", "adductor_resilience", "resilience"],
            "slots": [
                slot("mobility", ("adductor/groin", "adductors"), ("side lying groin stretch", "adductors"), ("groiners", "adductors")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Short Conditioning Top-Up",
            "focus": "keep repeat sprint exposure alive when the fixture list allows",
            "tags": ["repeat_sprint", "conditioning"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps")),
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("side hop-sprint", "quadriceps")),
                slot("mobility", ("hamstring stretch", None), ("adductor/groin", "adductors")),
            ],
        },
    ],
    "post_season": [
        {
            "label": "Restoration Session",
            "focus": "restore joints, adductors, hamstrings, and general movement options",
            "tags": ["mobility", "resilience", "adductor_resilience"],
            "slots": [
                slot("mobility", ("adductor/groin", "adductors"), ("side lying groin stretch", "adductors"), ("groiners", "adductors")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
            ],
        },
        {
            "label": "Tissue Rebuild",
            "focus": "rebuild lower-body force and soft-tissue tolerance",
            "tags": ["force", "hamstring_resilience", "resilience"],
            "slots": [
                slot("force", ("bodyweight walking lunge", "quadriceps"), ("split squat with dumbbells", "quadriceps")),
                slot("assistance", ("single leg glute bridge", "glutes"), ("standing dumbbell calf raise", "calves")),
                slot("assistance", ("hamstring stretch", "hamstrings"), ("adductor/groin", "adductors")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "General Reintroduction",
            "focus": "bridge recovery work back toward football-ready training",
            "tags": ["conditioning", "acceleration"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("single-cone sprint drill", "quadriceps")),
                slot("force", ("bodyweight walking lunge", "quadriceps"), ("split squat with dumbbells", "quadriceps")),
                slot("mobility", ("hamstring stretch", None), ("adductor/groin", "adductors")),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
            ],
        },
    ],
}

FOOTBALL_PHASE_LIBRARY = {
    "off_season": {
        "General Preparation": {
            "headline": "build tissue tolerance, force capacity, and running mechanics",
            "load_note": "moderate volume with weekly hamstring and adductor exposure",
            "roles": role_block(
                rx(4, "6-8", 90, 7), rx(3, "6-8", 75, 6), rx(3, "8-12", 60, 6), rx(4, "3-5", 75, 6),
                rx(5, "10-20m", 75, 6), rx(6, "15-20 sec", 45, 7), rx(3, "8-12", 30, 6), rx(2, "30-45 sec", 30, None),
            ),
        },
        "Max Velocity And Force": {
            "headline": "raise force and top-speed support while protecting hamstrings",
            "load_note": "lower reps on force work, longer rest on speed efforts",
            "roles": role_block(
                rx(5, "4-6", 120, 8), rx(3, "5-6", 75, 6), rx(3, "8-10", 60, 6), rx(4, "3-4", 90, 7),
                rx(6, "10-20m", 90, 7), rx(5, "12-15 sec", 60, 7), rx(3, "8-10", 30, 6), rx(2, "30-45 sec", 30, None),
            ),
        },
        "Football Power Conversion": {
            "headline": "convert strength into sharper accelerations and directional changes",
            "load_note": "pair force and speed with controlled total volume",
            "roles": role_block(
                rx(4, "4-5", 105, 7), rx(2, "5-6", 75, 6), rx(2, "8-10", 45, 6), rx(5, "2-4", 90, 7),
                rx(6, "10-15m", 90, 7), rx(5, "10-12 sec", 60, 7), rx(3, "8-10", 30, 6), rx(2, "30 sec", 30, None),
            ),
        },
        "Speed Realization": {
            "headline": "freshen fatigue and express speed, repeat sprint, and cutting quality",
            "load_note": "reduced volume with crisp speed actions",
            "roles": role_block(
                rx(3, "3-4", 90, 6), rx(2, "4-5", 60, 5), rx(2, "6-8", 45, 5), rx(4, "2-3", 90, 6),
                rx(4, "10m", 90, 6), rx(4, "8-10 sec", 60, 6), rx(2, "8-10", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
    },
    "pre_season": {
        "Specific Preparation": {
            "headline": "blend speed, repeated efforts, and football readiness",
            "load_note": "moderate volume with sharper football-specific intent",
            "roles": role_block(
                rx(4, "5-6", 90, 7), rx(3, "5-6", 75, 6), rx(2, "8-10", 45, 6), rx(4, "3-4", 75, 7),
                rx(5, "10-15m", 75, 7), rx(6, "10-15 sec", 45, 7), rx(3, "8-10", 30, 6), rx(2, "30 sec", 30, None),
            ),
        },
        "Match Fitness Integration": {
            "headline": "push repeat sprint readiness while preserving force and tissue quality",
            "load_note": "volume drops slightly while speed and density rise",
            "roles": role_block(
                rx(3, "4-5", 90, 7), rx(2, "5-6", 75, 6), rx(2, "8", 45, 6), rx(4, "2-4", 90, 7),
                rx(6, "10-15m", 90, 7), rx(6, "8-12 sec", 45, 7), rx(2, "8-10", 30, 6), rx(2, "30 sec", 30, None),
            ),
        },
        "Competition Readiness": {
            "headline": "preserve freshness and keep outputs sharp before competition",
            "load_note": "micro-dose force and speed with low residual soreness",
            "roles": role_block(
                rx(2, "3-4", 90, 6), rx(2, "4-5", 60, 5), rx(2, "6-8", 45, 5), rx(4, "2-3", 90, 6),
                rx(4, "10m", 90, 6), rx(4, "8-10 sec", 60, 6), rx(2, "8", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
    },
    "in_season": {
        "In-Season Maintenance": {
            "headline": "retain speed and force without creating match-week fatigue",
            "load_note": "micro-dose force and speed; keep mobility exposures frequent",
            "roles": role_block(
                rx(3, "3-5", 90, 7), rx(2, "4-6", 60, 5), rx(2, "6-8", 45, 5), rx(3, "2-3", 75, 6),
                rx(4, "10m", 75, 6), rx(4, "8-10 sec", 60, 6), rx(2, "8-10", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
        "Neural Freshness": {
            "headline": "keep acceleration and reactivity alive while reducing fatigue",
            "load_note": "very low volume, crisp sprint intent",
            "roles": role_block(
                rx(2, "3-4", 75, 6), rx(1, "4-5", 60, 5), rx(1, "6-8", 45, 4), rx(3, "2", 75, 6),
                rx(3, "5-10m", 75, 6), rx(3, "6-8 sec", 60, 5), rx(2, "8", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
        "Fixture Deload": {
            "headline": "bias recovery and tissue quality when match congestion is high",
            "load_note": "minimal dose, freshness first",
            "roles": role_block(
                rx(2, "3", 75, 5), rx(1, "4-5", 60, 4), rx(1, "6-8", 30, 4), rx(2, "2", 75, 5),
                rx(2, "5m", 60, 5), rx(2, "6 sec", 60, 4), rx(1, "8", 30, 4), rx(3, "30-45 sec", 30, None),
            ),
        },
    },
    "post_season": {
        "Restoration": {
            "headline": "restore joints, hamstrings, groins, and movement quality after competition",
            "load_note": "very low mechanical stress",
            "roles": role_block(
                rx(2, "6-8", 60, 5), rx(2, "6-8", 60, 5), rx(2, "8-10", 45, 5), rx(2, "3", 60, 5),
                rx(3, "10m", 60, 5), rx(4, "10 sec", 45, 5), rx(2, "8-10", 30, 5), rx(3, "30-45 sec", 30, None),
            ),
        },
        "Tissue Rebuild": {
            "headline": "gradually restore force, calf stiffness, and sprint support tissues",
            "load_note": "smooth progression with adductor and hamstring care kept in",
            "roles": role_block(
                rx(3, "6-8", 75, 6), rx(2, "6-8", 60, 5), rx(3, "8-12", 45, 6), rx(3, "3-4", 75, 6),
                rx(4, "10-15m", 75, 6), rx(4, "10-12 sec", 45, 6), rx(2, "8-10", 30, 5), rx(2, "30-45 sec", 30, None),
            ),
        },
        "General Reintroduction": {
            "headline": "bridge recovery work back to football-ready training",
            "load_note": "moderate volume with clean sprint mechanics",
            "roles": role_block(
                rx(3, "5-6", 75, 6), rx(2, "5-6", 60, 5), rx(2, "8-10", 45, 5), rx(3, "3", 75, 6),
                rx(4, "10m", 75, 6), rx(4, "10 sec", 45, 6), rx(2, "8-10", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
    },
}


def is_football_context(primary_sport: str | None, focus: str | None = None) -> bool:
    haystack = normalize_text(" ".join(filter(None, [primary_sport or "", focus or ""])))
    return any(keyword in haystack for keyword in FOOTBALL_KEYWORDS)


def build_football_strategy(
    context,
    goal,
    focus: str,
    duration_weeks: int,
    requested_sessions_per_week: int | None,
) -> dict[str, Any]:
    season_phase = normalize_season_phase(getattr(context, "season_phase", None))
    weekly_competitions = getattr(context, "weekly_competitions", None) or 0
    priorities = resolve_priorities(getattr(context, "performance_priorities", []), goal.title if goal else focus)
    session_count = resolve_session_count(season_phase, requested_sessions_per_week, weekly_competitions)
    constraints = build_constraints(
        season_phase=season_phase,
        weekly_competitions=weekly_competitions,
        session_count=session_count,
        session_duration_minutes=getattr(context, "session_duration_minutes", None),
    )
    return {
        "season_phase": season_phase,
        "weekly_competitions": weekly_competitions,
        "session_count": session_count,
        "phase_schedule": build_phase_schedule(duration_weeks, season_phase),
        "phase_library": FOOTBALL_PHASE_LIBRARY[season_phase],
        "templates": select_templates(season_phase, session_count, priorities),
        "priorities": priorities,
        "constraints": constraints,
        "max_slots_per_day": 4 if (getattr(context, "session_duration_minutes", 60) or 60) >= 55 else 3,
        "title": build_title(season_phase, focus, goal),
        "description": build_description(season_phase, focus, goal, priorities, constraints, duration_weeks),
    }


def normalize_season_phase(value: str | None) -> str:
    normalized = normalize_text(value or "").replace("-", " ").replace("_", " ").strip()
    return SEASON_PHASE_ALIASES.get(normalized, "off_season") if normalized else "off_season"


def resolve_priorities(values: list[str] | None, fallback_text: str | None) -> list[str]:
    raw_values = list(values or [])
    if fallback_text:
        raw_values.append(fallback_text)
    if not raw_values:
        return list(DEFAULT_PRIORITIES)

    resolved: list[str] = []
    for raw_value in raw_values:
        haystack = normalize_text(raw_value)
        for label, tags in PRIORITY_TAG_MAP.items():
            if label in haystack or any(tag in haystack for tag in tags):
                if label not in resolved:
                    resolved.append(label)

    return resolved or list(DEFAULT_PRIORITIES)


def resolve_session_count(season_phase: str, requested_sessions_per_week: int | None, weekly_competitions: int) -> int:
    config = SEASON_CONFIG[season_phase]
    session_count = requested_sessions_per_week or config["default_sessions"]
    if season_phase == "in_season" and weekly_competitions >= 2:
        session_count = min(session_count, 2)
    return max(1, min(session_count, config["max_sessions"]))


def build_phase_schedule(duration_weeks: int, season_phase: str) -> list[dict[str, Any]]:
    phase_names = {
        "off_season": build_off_season_phases(duration_weeks),
        "pre_season": build_pre_season_phases(duration_weeks),
        "in_season": build_in_season_phases(duration_weeks),
        "post_season": build_post_season_phases(duration_weeks),
    }[season_phase]
    library = FOOTBALL_PHASE_LIBRARY[season_phase]
    return [
        {
            "week_index": week_index,
            "phase_name": phase_name,
            "headline": library[phase_name]["headline"],
            "load_note": library[phase_name]["load_note"],
        }
        for week_index, phase_name in enumerate(phase_names, start=1)
    ]


def build_off_season_phases(duration_weeks: int) -> list[str]:
    if duration_weeks <= 4:
        return [
            "General Preparation",
            "Max Velocity And Force",
            "Football Power Conversion",
            "Speed Realization",
        ][:duration_weeks]

    prep = 2 if duration_weeks >= 7 else 1
    realization = 1
    remaining = max(0, duration_weeks - prep - realization)
    strength = max(1, ceil(remaining * 0.55))
    conversion = max(1, remaining - strength)
    while prep + strength + conversion + realization > duration_weeks:
        if strength > conversion:
            strength -= 1
        else:
            conversion -= 1
    return (
        ["General Preparation"] * prep
        + ["Max Velocity And Force"] * strength
        + ["Football Power Conversion"] * conversion
        + ["Speed Realization"] * realization
    )[:duration_weeks]


def build_pre_season_phases(duration_weeks: int) -> list[str]:
    if duration_weeks == 1:
        return ["Specific Preparation"]
    if duration_weeks == 2:
        return ["Specific Preparation", "Competition Readiness"]
    if duration_weeks == 3:
        return ["Specific Preparation", "Match Fitness Integration", "Competition Readiness"]
    return (
        ["Specific Preparation"]
        + ["Match Fitness Integration"] * max(1, duration_weeks - 2)
        + ["Competition Readiness"]
    )[:duration_weeks]


def build_in_season_phases(duration_weeks: int) -> list[str]:
    if duration_weeks == 1:
        return ["In-Season Maintenance"]
    if duration_weeks == 2:
        return ["In-Season Maintenance", "Fixture Deload"]
    phases = []
    for week_index in range(1, duration_weeks + 1):
        if week_index == duration_weeks:
            phases.append("Fixture Deload")
        elif week_index % 2 == 0:
            phases.append("Neural Freshness")
        else:
            phases.append("In-Season Maintenance")
    return phases


def build_post_season_phases(duration_weeks: int) -> list[str]:
    if duration_weeks == 1:
        return ["Restoration"]
    if duration_weeks == 2:
        return ["Restoration", "Tissue Rebuild"]
    return (
        ["Restoration"]
        + ["Tissue Rebuild"] * max(1, duration_weeks - 2)
        + ["General Reintroduction"]
    )[:duration_weeks]


def build_constraints(
    season_phase: str,
    weekly_competitions: int,
    session_count: int,
    session_duration_minutes: int | None,
) -> list[str]:
    constraints: list[str] = []
    if season_phase == "off_season":
        constraints.extend(
            [
                "Keep weekly hamstring, groin, and calf resilience exposures while building force and speed.",
                "Bias acceleration and repeat sprint foundations before dense match-like conditioning.",
            ]
        )
    elif season_phase == "pre_season":
        constraints.extend(
            [
                "Reduce bodybuilding-style fatigue and bias match speed, repeat sprint ability, and tissue freshness.",
                "Retain weekly hamstring and adductor support as intensity rises.",
            ]
        )
    elif season_phase == "in_season":
        constraints.extend(
            [
                "Cap soreness and eccentric stress so the athlete stays fresh for training and matches.",
                "Use micro-dosed force and sprint work around competition density.",
            ]
        )
    else:
        constraints.extend(
            [
                "Prioritise restoration, mobility, and gradual force reintroduction after the season.",
                "Do not chase peak sprint outputs until soft-tissue quality returns.",
            ]
        )

    if weekly_competitions >= 2:
        constraints.append("High fixture density means the plan should stay at or below two support sessions weekly.")
    if session_duration_minutes and session_duration_minutes < 50:
        constraints.append("Short sessions should prioritise speed, hamstrings, and groin support before accessories.")
    if session_count >= 5:
        constraints.append("Only two sessions in the week should carry high sprint or elastic demand.")
    return constraints


def build_title(season_phase: str, focus: str, goal) -> str:
    phase_label = season_phase.replace("_", " ").title()
    return f"Football {phase_label} - {(goal.title if goal else focus).title()}"


def build_description(
    season_phase: str,
    focus: str,
    goal,
    priorities: list[str],
    constraints: list[str],
    duration_weeks: int,
) -> str:
    goal_title = goal.title if goal else focus
    return (
        f"Sport-specific football plan for the {season_phase.replace('_', ' ')} phase. "
        f"Primary direction: {goal_title}. Priority qualities: {', '.join(priorities[:3])}. "
        f"The cycle uses Bompa-style sequencing across {duration_weeks} weeks and adapts weekly stress "
        f"to football needs like acceleration, repeat sprint ability, change of direction, and hamstring or adductor resilience. "
        f"{' '.join(constraints[:2])}"
    )


def select_templates(season_phase: str, session_count: int, priorities: list[str]) -> list[dict[str, Any]]:
    priority_tags = resolve_priority_tags(priorities)
    ranked = sorted(
        enumerate(FOOTBALL_TEMPLATE_LIBRARY[season_phase]),
        key=lambda item: (score_template(item[1], priority_tags), -item[0]),
        reverse=True,
    )
    selected = [template for _, template in ranked[:session_count]]
    if len(selected) < session_count:
        library = FOOTBALL_TEMPLATE_LIBRARY[season_phase]
        while len(selected) < session_count:
            selected.append(library[len(selected) % len(library)])
    return selected


def resolve_priority_tags(priorities: list[str]) -> set[str]:
    tags = set()
    for priority in priorities:
        tags.update(PRIORITY_TAG_MAP.get(priority, ()))
    return tags


def score_template(template: dict[str, Any], priority_tags: set[str]) -> int:
    template_tags = set(template.get("tags", []))
    return (len(template_tags & priority_tags) * 3) + (1 if "mobility" in template_tags else 0)
