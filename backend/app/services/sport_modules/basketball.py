from __future__ import annotations

from math import ceil
from typing import Any

from app.utils.normalizer import normalize_text


BASKETBALL_KEYWORDS = (
    "basketball",
    "hoops",
    "point guard",
    "shooting guard",
    "guard",
    "forward",
    "center",
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
    "vertical power": ("vertical_power", "elastic"),
    "jump": ("vertical_power", "elastic"),
    "vertical": ("vertical_power", "elastic"),
    "first step": ("acceleration", "speed"),
    "acceleration": ("acceleration", "speed"),
    "change of direction": ("change_of_direction", "speed"),
    "cod": ("change_of_direction", "speed"),
    "agility": ("change_of_direction", "speed"),
    "deceleration": ("change_of_direction", "force"),
    "repeat sprint": ("repeat_sprint", "conditioning"),
    "conditioning": ("repeat_sprint", "conditioning"),
    "contact": ("upper_body", "resilience"),
    "resilience": ("upper_body", "resilience"),
}

DEFAULT_PRIORITIES = [
    "vertical power",
    "first step",
    "change of direction",
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


BASKETBALL_TEMPLATE_LIBRARY = {
    "off_season": [
        {
            "label": "Force And Landing Mechanics",
            "focus": "lower-body force, eccentric control, and clean landings",
            "tags": ["force", "vertical_power", "change_of_direction"],
            "slots": [
                slot("force", ("split squat with dumbbells", "quadriceps"), ("goblet squat", "quadriceps"), ("bodyweight walking lunge", "quadriceps")),
                slot("force", ("romanian deadlift", "hamstrings"), ("single leg glute bridge", "glutes"), ("dumbbell rear lunge", "quadriceps")),
                slot("elastic", ("freehand jump squat", "quadriceps"), ("front box jump", "hamstrings"), ("lateral box jump", "adductors")),
                slot("core", ("plank", "abdominals"), ("reverse crunch", "abdominals")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
            ],
        },
        {
            "label": "Upper Body Resilience",
            "focus": "upper-body strength, contact tolerance, and trunk stiffness",
            "tags": ["upper_body", "resilience"],
            "slots": [
                slot("upper_strength", ("pushups", "chest"), ("push up to side plank", "chest")),
                slot("upper_strength", ("one-arm dumbbell row", "middle back"), ("bent over two-dumbbell row", "middle back"), ("inverted row", "middle back")),
                slot("elastic", ("medicine ball chest pass", "chest"), ("medicine ball scoop throw", "shoulders"), ("pushups", "chest")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
                slot("mobility", ("seated overhead stretch", None), ("hamstring stretch", None)),
            ],
        },
        {
            "label": "Acceleration And COD",
            "focus": "first-step force, braking quality, and directional efficiency",
            "tags": ["acceleration", "change_of_direction"],
            "slots": [
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("side hop-sprint", "quadriceps"), ("wind sprints", "abdominals")),
                slot("force", ("crossover reverse lunge", "quadriceps"), ("bodyweight walking lunge", "quadriceps"), ("split squats", "quadriceps")),
                slot("elastic", ("freehand jump squat", "quadriceps"), ("lateral box jump", "adductors"), ("front box jump", "hamstrings")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
                slot("mobility", ("hamstring stretch", None), ("hip flexor stretch", None)),
            ],
        },
        {
            "label": "Jump Power And Repeat Sprint",
            "focus": "jump expression and short-burst conditioning tolerance",
            "tags": ["vertical_power", "repeat_sprint"],
            "slots": [
                slot("elastic", ("freehand jump squat", "quadriceps"), ("front box jump", "hamstrings"), ("lateral box jump", "adductors")),
                slot("elastic", ("medicine ball scoop throw", "shoulders"), ("medicine ball chest pass", "chest"), ("pushups", "chest")),
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps"), ("single-cone sprint drill", "quadriceps")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
            ],
        },
    ],
    "pre_season": [
        {
            "label": "Power Transfer Day",
            "focus": "convert force into jump and acceleration outputs",
            "tags": ["vertical_power", "acceleration"],
            "slots": [
                slot("force", ("split squat with dumbbells", "quadriceps"), ("dumbbell rear lunge", "quadriceps")),
                slot("elastic", ("freehand jump squat", "quadriceps"), ("front box jump", "hamstrings")),
                slot("speed", ("side hop-sprint", "quadriceps"), ("single-cone sprint drill", "quadriceps"), ("wind sprints", "abdominals")),
                slot("core", ("plank", "abdominals"), ("reverse crunch", "abdominals")),
            ],
        },
        {
            "label": "Strength Maintenance And Contact",
            "focus": "retain strength and upper-body robustness before competition",
            "tags": ["upper_body", "resilience"],
            "slots": [
                slot("upper_strength", ("pushups", "chest"), ("push up to side plank", "chest")),
                slot("upper_strength", ("one-arm dumbbell row", "middle back"), ("bent over two-dumbbell row", "middle back")),
                slot("assistance", ("standing dumbbell calf raise", "calves"), ("single leg glute bridge", "glutes")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Repeat Sprint Readiness",
            "focus": "prepare for repeated high-intensity efforts and short recoveries",
            "tags": ["repeat_sprint", "conditioning"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps"), ("single-cone sprint drill", "quadriceps")),
                slot("speed", ("side hop-sprint", "quadriceps"), ("wind sprints", "abdominals")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Mobility And Freshness",
            "focus": "keep hips, ankles, and trunk fresh while protecting jump quality",
            "tags": ["mobility", "resilience"],
            "slots": [
                slot("mobility", ("hamstring stretch", None), ("seated overhead stretch", None)),
                slot("assistance", ("single leg glute bridge", "glutes"), ("standing dumbbell calf raise", "calves")),
                slot("core", ("plank", "abdominals"), ("reverse crunch", "abdominals")),
            ],
        },
    ],
    "in_season": [
        {
            "label": "Neural Primer",
            "focus": "keep the nervous system sharp without adding fatigue",
            "tags": ["vertical_power", "acceleration"],
            "slots": [
                slot("elastic", ("freehand jump squat", "quadriceps"), ("front box jump", "hamstrings")),
                slot("speed", ("single-cone sprint drill", "quadriceps"), ("wind sprints", "abdominals")),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
            ],
        },
        {
            "label": "Strength Maintenance",
            "focus": "micro-dose lower and upper strength around games",
            "tags": ["force", "upper_body"],
            "slots": [
                slot("force", ("split squat with dumbbells", "quadriceps"), ("bodyweight walking lunge", "quadriceps")),
                slot("upper_strength", ("pushups", "chest"), ("one-arm dumbbell row", "middle back")),
                slot("assistance", ("standing dumbbell calf raise", "calves"), ("single leg glute bridge", "glutes")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Recovery And Mobility",
            "focus": "restore range of motion and reduce soreness between games",
            "tags": ["mobility", "resilience"],
            "slots": [
                slot("mobility", ("hamstring stretch", None), ("seated overhead stretch", None)),
                slot("assistance", ("single leg glute bridge", "glutes"), ("standing dumbbell calf raise", "calves")),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Short Sprint Support",
            "focus": "keep conditioning exposure alive without burying the athlete",
            "tags": ["repeat_sprint", "conditioning"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
    ],
    "post_season": [
        {
            "label": "Restoration Session",
            "focus": "restore movement options and reduce accumulated fatigue",
            "tags": ["mobility", "resilience"],
            "slots": [
                slot("mobility", ("hamstring stretch", None), ("seated overhead stretch", None)),
                slot("core", ("plank", "abdominals"), ("side bridge", "abdominals")),
                slot("assistance", ("single leg glute bridge", "glutes"), ("standing dumbbell calf raise", "calves")),
            ],
        },
        {
            "label": "General Strength Rebuild",
            "focus": "rebuild tissue tolerance before a new development block",
            "tags": ["force", "upper_body"],
            "slots": [
                slot("force", ("bodyweight walking lunge", "quadriceps"), ("split squat with dumbbells", "quadriceps")),
                slot("upper_strength", ("pushups", "chest"), ("one-arm dumbbell row", "middle back")),
                slot("core", ("reverse crunch", "abdominals"), ("plank", "abdominals")),
            ],
        },
        {
            "label": "Low-Impact Conditioning",
            "focus": "keep a baseline work capacity without court-level fatigue",
            "tags": ["conditioning", "repeat_sprint"],
            "slots": [
                slot("conditioning", ("wind sprints", "abdominals"), ("bench sprint", "quadriceps")),
                slot("mobility", ("hamstring stretch", None), ("seated floor hamstring stretch", None)),
                slot("core", ("side bridge", "abdominals"), ("plank", "abdominals")),
            ],
        },
    ],
}

BASKETBALL_PHASE_LIBRARY = {
    "off_season": {
        "General Preparation": {
            "headline": "build tissue tolerance, foundational strength, and landing control",
            "load_note": "moderate volume with careful eccentric exposure",
            "roles": role_block(
                rx(4, "6-8", 90, 7), rx(4, "6-8", 75, 7), rx(3, "8-12", 60, 6), rx(4, "3-5", 75, 6),
                rx(5, "10-20m", 75, 6), rx(6, "15-20 sec", 45, 7), rx(3, "8-12", 30, 6), rx(2, "30-45 sec", 30, None),
            ),
        },
        "Max Strength Development": {
            "headline": "raise force output that later converts to acceleration and jumping",
            "load_note": "lower reps, higher intent, longer rest on force lifts",
            "roles": role_block(
                rx(5, "4-6", 120, 8), rx(4, "5-6", 90, 7), rx(3, "8-10", 60, 6), rx(4, "3-4", 90, 7),
                rx(5, "10-20m", 90, 7), rx(5, "15 sec", 60, 7), rx(3, "8-10", 30, 6), rx(2, "30-45 sec", 30, None),
            ),
        },
        "Force To Power Conversion": {
            "headline": "convert force into faster jumps and sharper cuts",
            "load_note": "pair crisp force work with explosive outputs",
            "roles": role_block(
                rx(4, "4-5", 120, 7), rx(3, "5-6", 75, 7), rx(2, "8-10", 45, 6), rx(5, "2-4", 90, 7),
                rx(6, "10-15m", 90, 7), rx(5, "10-15 sec", 60, 7), rx(3, "8-10", 30, 6), rx(2, "30 sec", 30, None),
            ),
        },
        "Basketball Power Realization": {
            "headline": "freshen fatigue and express speed, jump quality, and reactive sharpness",
            "load_note": "reduced volume with high-quality explosive contacts",
            "roles": role_block(
                rx(3, "3-4", 120, 6), rx(2, "4-6", 75, 6), rx(2, "6-8", 45, 5), rx(4, "2-3", 90, 6),
                rx(4, "10-15m", 90, 6), rx(4, "10-12 sec", 60, 6), rx(2, "8-10", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
    },
    "pre_season": {
        "Specific Preparation": {
            "headline": "blend power, acceleration, and conditioning toward basketball demands",
            "load_note": "moderate volume with sharp movement quality",
            "roles": role_block(
                rx(4, "5-6", 90, 7), rx(3, "5-6", 75, 7), rx(2, "8-10", 45, 6), rx(4, "3-4", 75, 7),
                rx(5, "10-15m", 75, 7), rx(6, "10-15 sec", 45, 7), rx(3, "8-10", 30, 6), rx(2, "30 sec", 30, None),
            ),
        },
        "Power And Speed Integration": {
            "headline": "bias explosive outputs while preserving force and court repeatability",
            "load_note": "lower volume than off-season, more court-speed intent",
            "roles": role_block(
                rx(3, "4-5", 90, 7), rx(3, "4-5", 75, 7), rx(2, "8", 45, 6), rx(5, "2-4", 90, 7),
                rx(6, "10-15m", 90, 7), rx(5, "8-12 sec", 45, 7), rx(2, "8-10", 30, 6), rx(2, "30 sec", 30, None),
            ),
        },
        "Competition Readiness": {
            "headline": "preserve freshness and keep outputs crisp entering competition",
            "load_note": "micro-dose strength and keep contacts explosive, not exhaustive",
            "roles": role_block(
                rx(2, "3-4", 90, 6), rx(2, "4-5", 60, 6), rx(2, "6-8", 45, 5), rx(4, "2-3", 90, 6),
                rx(4, "10m", 90, 6), rx(4, "8-10 sec", 60, 6), rx(2, "8", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
    },
    "in_season": {
        "In-Season Maintenance": {
            "headline": "retain force qualities without creating heavy soreness before games",
            "load_note": "micro-dose strength and keep jump contacts low",
            "roles": role_block(
                rx(3, "3-5", 90, 7), rx(2, "4-6", 60, 6), rx(2, "6-8", 45, 5), rx(3, "2-3", 75, 6),
                rx(4, "10m", 75, 6), rx(4, "8-10 sec", 60, 6), rx(2, "8-10", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
        "Neural Freshness": {
            "headline": "keep acceleration and jump reactivity alive while reducing fatigue",
            "load_note": "very low volume, very crisp intent",
            "roles": role_block(
                rx(2, "3-4", 75, 6), rx(2, "4-5", 60, 5), rx(1, "6-8", 45, 5), rx(3, "2", 75, 6),
                rx(3, "5-10m", 75, 6), rx(3, "6-8 sec", 60, 5), rx(2, "8", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
        "Game Support Deload": {
            "headline": "bias recovery and tissue quality around dense game calendars",
            "load_note": "minimal dose, freshness first",
            "roles": role_block(
                rx(2, "3", 75, 5), rx(1, "4-5", 60, 5), rx(1, "6-8", 30, 4), rx(2, "2", 75, 5),
                rx(2, "5m", 60, 5), rx(2, "6 sec", 60, 4), rx(1, "8", 30, 4), rx(3, "30-45 sec", 30, None),
            ),
        },
    },
    "post_season": {
        "Restoration": {
            "headline": "restore joints, soft tissue, and movement variability after competition",
            "load_note": "very low mechanical stress",
            "roles": role_block(
                rx(2, "6-8", 60, 5), rx(2, "6-8", 60, 5), rx(2, "8-10", 45, 5), rx(2, "3", 60, 5),
                rx(3, "10m", 60, 5), rx(4, "10 sec", 45, 5), rx(2, "8-10", 30, 5), rx(3, "30-45 sec", 30, None),
            ),
        },
        "Tissue Rebuild": {
            "headline": "gradually reintroduce strength and stiffness qualities",
            "load_note": "moderate effort, smooth progression",
            "roles": role_block(
                rx(3, "6-8", 75, 6), rx(3, "6-8", 60, 6), rx(3, "8-12", 45, 6), rx(3, "3-4", 75, 6),
                rx(4, "10-15m", 75, 6), rx(4, "10-12 sec", 45, 6), rx(2, "8-10", 30, 5), rx(2, "30-45 sec", 30, None),
            ),
        },
        "General Reintroduction": {
            "headline": "bridge from recovery work back to full development training",
            "load_note": "moderate volume with clean technical execution",
            "roles": role_block(
                rx(3, "5-6", 75, 6), rx(3, "5-6", 60, 6), rx(2, "8-10", 45, 5), rx(3, "3", 75, 6),
                rx(4, "10m", 75, 6), rx(4, "10 sec", 45, 6), rx(2, "8-10", 30, 5), rx(2, "30 sec", 30, None),
            ),
        },
    },
}


def is_basketball_context(primary_sport: str | None, focus: str | None = None) -> bool:
    haystack = normalize_text(" ".join(filter(None, [primary_sport or "", focus or ""])))
    return any(keyword in haystack for keyword in BASKETBALL_KEYWORDS)


def build_basketball_strategy(
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
        "phase_library": BASKETBALL_PHASE_LIBRARY[season_phase],
        "templates": select_templates(season_phase, session_count, priorities),
        "priorities": priorities,
        "constraints": constraints,
        "max_slots_per_day": 4 if (getattr(context, "session_duration_minutes", 60) or 60) >= 55 else 3,
        "title": build_title(season_phase, focus, goal),
        "description": build_description(
            season_phase,
            focus,
            goal,
            priorities,
            constraints,
            duration_weeks,
        ),
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
        session_count = min(session_count, 3)
    return max(1, min(session_count, config["max_sessions"]))


def build_phase_schedule(duration_weeks: int, season_phase: str) -> list[dict[str, Any]]:
    phase_names = {
        "off_season": build_off_season_phases(duration_weeks),
        "pre_season": build_pre_season_phases(duration_weeks),
        "in_season": build_in_season_phases(duration_weeks),
        "post_season": build_post_season_phases(duration_weeks),
    }[season_phase]
    library = BASKETBALL_PHASE_LIBRARY[season_phase]
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
            "Max Strength Development",
            "Force To Power Conversion",
            "Basketball Power Realization",
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
        + ["Max Strength Development"] * strength
        + ["Force To Power Conversion"] * conversion
        + ["Basketball Power Realization"] * realization
    )[:duration_weeks]


def build_pre_season_phases(duration_weeks: int) -> list[str]:
    if duration_weeks == 1:
        return ["Specific Preparation"]
    if duration_weeks == 2:
        return ["Specific Preparation", "Competition Readiness"]
    if duration_weeks == 3:
        return ["Specific Preparation", "Power And Speed Integration", "Competition Readiness"]
    return (
        ["Specific Preparation"]
        + ["Power And Speed Integration"] * max(1, duration_weeks - 2)
        + ["Competition Readiness"]
    )[:duration_weeks]


def build_in_season_phases(duration_weeks: int) -> list[str]:
    if duration_weeks == 1:
        return ["In-Season Maintenance"]
    if duration_weeks == 2:
        return ["In-Season Maintenance", "Neural Freshness"]
    phases = []
    for week_index in range(1, duration_weeks + 1):
        if week_index == duration_weeks:
            phases.append("Game Support Deload")
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
                "Bias lower-body force and landing quality before dense plyometric volume.",
                "Keep at least one weekly exposure for trunk and calf stiffness.",
            ]
        )
    elif season_phase == "pre_season":
        constraints.extend(
            [
                "Reduce hypertrophy-style fatigue and bias speed, power, and repeatability.",
                "Keep acceleration and jump contacts crisp rather than exhaustive.",
            ]
        )
    elif season_phase == "in_season":
        constraints.extend(
            [
                "Cap soreness and eccentric stress so the athlete stays fresh for practices and games.",
                "Use micro-dosed strength and low-contact power exposures around competition.",
            ]
        )
    else:
        constraints.extend(
            [
                "Prioritise restoration, tissue quality, and gradual reintroduction of load.",
                "Do not chase peak outputs until recovery quality is back.",
            ]
        )

    if weekly_competitions >= 2:
        constraints.append("Competition density is high, so support work should stay at or below three sessions weekly.")
    if session_duration_minutes and session_duration_minutes < 50:
        constraints.append("Short sessions should prioritise the first two slots and trim accessory work.")
    if session_count >= 5:
        constraints.append("Only two sessions in the week should carry high neural demand.")
    return constraints


def build_title(season_phase: str, focus: str, goal) -> str:
    phase_label = season_phase.replace("_", " ").title()
    return f"Basketball {phase_label} - {(goal.title if goal else focus).title()}"


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
        f"Sport-specific basketball plan for the {season_phase.replace('_', ' ')} phase. "
        f"Primary direction: {goal_title}. Priority qualities: {', '.join(priorities[:3])}. "
        f"The cycle uses Bompa-style sequencing across {duration_weeks} weeks and adapts weekly stress "
        f"to basketball needs like jump quality, acceleration, change of direction, and repeat sprint tolerance. "
        f"{' '.join(constraints[:2])}"
    )


def select_templates(season_phase: str, session_count: int, priorities: list[str]) -> list[dict[str, Any]]:
    priority_tags = resolve_priority_tags(priorities)
    ranked = sorted(
        enumerate(BASKETBALL_TEMPLATE_LIBRARY[season_phase]),
        key=lambda item: (score_template(item[1], priority_tags), -item[0]),
        reverse=True,
    )
    selected = [template for _, template in ranked[:session_count]]
    if len(selected) < session_count:
        library = BASKETBALL_TEMPLATE_LIBRARY[season_phase]
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
