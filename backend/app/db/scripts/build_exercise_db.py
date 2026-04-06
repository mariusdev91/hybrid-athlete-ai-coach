import json
import uuid
import re
from pathlib import Path
from jsonschema import validate, ValidationError


BASE_DIR = Path(__file__).resolve().parent.parent
FREE_COMBINED = BASE_DIR / "free-exercise-db" / "combined.json"
SCHEMA_FILE = BASE_DIR / "open-exercise-db" / "exercise.schema.json"
OUTPUT_FILE = BASE_DIR / "exercises.json"


def normalize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[\(\)\-_/]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def load_free_combined():
    with open(FREE_COMBINED, "r", encoding="utf-8") as f:
        return json.load(f)


def load_schema():
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_final_json():
    free_data = load_free_combined()
    schema = load_schema()

    final = []

    for entry in free_data:
        normalized_name = normalize_name(entry["name"])

        unified = {
            "id": str(uuid.uuid4()),
            "name": entry["name"],
            "primary_muscles": entry.get("primaryMuscles", []),
            "secondary_muscles": entry.get("secondaryMuscles", []),
            "equipment": entry.get("equipment", None),
            "instructions": entry.get("instructions", []),
            "coaching_cues": [],
            "contraindications": [],
            "progressions": [],
            "regressions": [],
            "images": [],
            "source": ["free"]
        }

        # validate against schema (optional fields allowed)
        try:
            validate(unified, schema)
        except ValidationError as e:
            print(f"Validation warning for {entry['name']}: {e.message}")

        final.append(unified)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(final)} exercises → {OUTPUT_FILE}")


if __name__ == "__main__":
    build_final_json()
