from __future__ import annotations

from app.utils.normalizer import normalize_text


LOW_SIGNAL_ANSWERS = {
    "cel de mai sus",
    "cea de mai sus",
    "cele de mai sus",
    "de mai sus",
    "mai sus",
    "acelasi",
    "aceeasi",
    "idem",
    "same as above",
    "as above",
    "same",
    "above",
}

REQUEST_STYLE_PREFIXES = (
    "vreau",
    "as vrea",
    "doresc",
    "i want",
    "help me",
    "give me",
    "build me",
    "make me",
)


PRIMARY_SPORT_ALIASES = {
    "football": "football",
    "soccer": "football",
    "fotbal": "football",
    "basketball": "basketball",
    "baschet": "basketball",
    "hoops": "basketball",
}


SEASON_PHASE_ALIASES = {
    "off_season": "off_season",
    "off season": "off_season",
    "offseason": "off_season",
    "extrasezon": "off_season",
    "extra sezon": "off_season",
    "pre_season": "pre_season",
    "pre season": "pre_season",
    "preseason": "pre_season",
    "presezon": "pre_season",
    "in_season": "in_season",
    "in season": "in_season",
    "inseason": "in_season",
    "sezon": "in_season",
    "in sezon": "in_season",
    "post_season": "post_season",
    "post season": "post_season",
    "postseason": "post_season",
    "postsezon": "post_season",
}


GOAL_TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("performance", ("performance", "performanta", "sport performance", "athletic performance")),
    ("strength", ("strength", "forta")),
    ("endurance", ("endurance", "conditioning", "cardio", "stamina", "rezistenta")),
    ("fat loss", ("fat loss", "weight loss", "slabire", "cut")),
    ("mobility", ("mobility", "mobilitate")),
    ("recovery", ("recovery", "recuperare", "regen", "restore")),
)


GOAL_TYPE_DEFAULT_LABELS = {
    "performance": "performance development",
    "strength": "strength development",
    "endurance": "conditioning development",
    "fat loss": "body composition support",
    "mobility": "mobility support",
    "recovery": "recovery and tissue quality",
}


SPORT_DISPLAY_LABELS = {
    "football": "Football",
    "basketball": "Basketball",
}


def normalize_primary_sport(value: str | None) -> str | None:
    normalized = normalize_text(value or "").strip()
    if not normalized:
        return None
    return PRIMARY_SPORT_ALIASES.get(normalized, normalized)


def normalize_season_phase(value: str | None) -> str | None:
    normalized = normalize_text(value or "").replace("-", " ").replace("_", " ").strip()
    if not normalized:
        return None
    return SEASON_PHASE_ALIASES.get(normalized, normalized.replace(" ", "_"))


def normalize_goal_type(value: str | None) -> str:
    normalized = normalize_text(value or "").strip()
    if not normalized:
        return "performance"

    for canonical, keywords in GOAL_TYPE_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return canonical
    return "performance"


def is_low_signal_answer(value: str | None) -> bool:
    normalized = normalize_text(value or "").strip()
    if not normalized:
        return True
    return normalized in LOW_SIGNAL_ANSWERS


def sanitize_goal_title(
    value: str | None,
    *,
    fallback_text: str | None = None,
    primary_sport: str | None = None,
    goal_type: str | None = None,
) -> str:
    if is_goal_title_candidate(value):
        return value.strip()

    if is_goal_title_candidate(fallback_text):
        return fallback_text.strip()

    normalized_goal_type = normalize_goal_type(goal_type)
    default_label = GOAL_TYPE_DEFAULT_LABELS[normalized_goal_type]
    sport_label = SPORT_DISPLAY_LABELS.get(normalize_primary_sport(primary_sport) or "")
    if sport_label:
        return f"{sport_label} {default_label}"
    return default_label.capitalize()


def is_goal_title_candidate(value: str | None) -> bool:
    if not value or is_low_signal_answer(value):
        return False

    normalized = normalize_text(value).strip()
    if not normalized:
        return False
    if any(normalized.startswith(prefix) for prefix in REQUEST_STYLE_PREFIXES):
        return False
    if len(normalized.split()) > 10:
        return False
    return True
