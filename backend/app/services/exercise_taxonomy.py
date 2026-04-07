from __future__ import annotations

from app.utils.normalizer import normalize_text


TAG_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("plyometric", ("jump", "hop", "bound", "depth jump", "box jump")),
    ("vertical_power", ("jump squat", "box jump", "depth jump", "knee tuck jump", "rocket jump")),
    ("horizontal_power", ("standing long jump", "stride jump", "bound")),
    ("lateral_power", ("lateral", "side hop", "cone hops")),
    ("acceleration", ("sprint", "first step", "10m", "cone sprint")),
    ("max_speed", ("wind sprints", "sprint")),
    ("change_of_direction", ("lateral", "crossover", "side hop", "cone", "bound")),
    ("repeat_sprint", ("wind sprints", "bench sprint", "prowler sprint", "sprint")),
    ("deceleration", ("landing", "depth jump", "bound", "lunge")),
    ("lower_strength", ("squat", "lunge", "split squat")),
    ("unilateral_lower", ("single-leg", "split squat", "lunge", "rear lunge")),
    ("posterior_chain", ("hamstring", "glute bridge", "deadlift")),
    ("hamstring_resilience", ("hamstring", "slides", "leg curl")),
    ("adductor_resilience", ("adductor", "groin")),
    ("calf_stiffness", ("calf",)),
    ("upper_push", ("push", "press")),
    ("upper_pull", ("row", "pull")),
    ("medicine_ball_power", ("medicine ball", "slam", "throw")),
    ("trunk_stability", ("plank", "bridge", "crunch", "wood chop")),
    ("mobility", ("stretch", "smr")),
    ("recovery", ("stretch", "smr")),
)

FAMILY_PRIORITY: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("plyometric", ("plyometric", "vertical_power", "horizontal_power", "lateral_power")),
    ("speed", ("acceleration", "max_speed", "repeat_sprint", "change_of_direction")),
    ("adductor", ("adductor_resilience",)),
    ("calf", ("calf_stiffness",)),
    ("lower_strength", ("lower_strength", "unilateral_lower")),
    ("posterior_chain", ("posterior_chain", "hamstring_resilience")),
    ("upper_push", ("upper_push",)),
    ("upper_pull", ("upper_pull",)),
    ("medicine_ball_power", ("medicine_ball_power",)),
    ("trunk", ("trunk_stability",)),
    ("mobility", ("mobility", "recovery")),
)


def infer_exercise_tags(
    *,
    name: str | None,
    query: str | None = None,
    equipment: str | None = None,
    primary_muscles: list[str] | None = None,
    secondary_muscles: list[str] | None = None,
) -> set[str]:
    text = normalize_text(
        " ".join(
            filter(
                None,
                [
                    name or "",
                    query or "",
                    equipment or "",
                    " ".join(primary_muscles or []),
                    " ".join(secondary_muscles or []),
                ],
            )
        )
    )
    tags: set[str] = set()

    for tag, keywords in TAG_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            tags.add(tag)

    if "split squat" in text or "rear lunge" in text or "walking lunge" in text:
        tags.update({"lower_strength", "unilateral_lower"})
    if "glute bridge" in text:
        tags.update({"posterior_chain", "unilateral_lower"})
    if "plank" in text or "bridge" in text:
        tags.add("trunk_stability")
    if "medicine ball" in text:
        tags.add("medicine_ball_power")
    if "stretch" in text or "smr" in text:
        tags.update({"mobility", "recovery"})

    return tags


def infer_primary_family(tags: set[str]) -> str:
    for family, required_tags in FAMILY_PRIORITY:
        if any(tag in tags for tag in required_tags):
            return family
    return "general"
