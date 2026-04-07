from app.services.exercise_taxonomy import infer_exercise_tags
from app.services.exercise_taxonomy import infer_primary_family


def test_infer_exercise_tags_for_plyometric_speed_drill():
    tags = infer_exercise_tags(
        name="Depth Jump Leap",
        query="depth jump leap",
        equipment="body only",
        primary_muscles=["quadriceps"],
        secondary_muscles=["calves"],
    )

    assert "plyometric" in tags
    assert "vertical_power" in tags
    assert infer_primary_family(tags) == "plyometric"


def test_infer_exercise_tags_for_adductor_mobility_drill():
    tags = infer_exercise_tags(
        name="Side Lying Groin Stretch",
        query="groin stretch",
        primary_muscles=["adductors"],
        secondary_muscles=["hamstrings"],
    )

    assert "adductor_resilience" in tags
    assert "mobility" in tags
    assert infer_primary_family(tags) == "adductor"


def test_infer_exercise_tags_for_sprint_drill():
    tags = infer_exercise_tags(
        name="Single-Cone Sprint Drill",
        query="single-cone sprint drill",
        equipment="body only",
        primary_muscles=["quadriceps"],
        secondary_muscles=["hamstrings", "calves"],
    )

    assert "acceleration" in tags
    assert "repeat_sprint" in tags
    assert infer_primary_family(tags) == "speed"
