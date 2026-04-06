import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FREE_EX_DIR = BASE_DIR / "free-exercise-db" / "exercises"
OUTPUT = BASE_DIR / "free-exercise-db" / "combined.json"


def build_free_combined():
    all_exercises = []

    for file in FREE_EX_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_exercises.append(data)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_exercises, f, indent=2, ensure_ascii=False)

    print(f"Generated combined.json with {len(all_exercises)} exercises → {OUTPUT}")


if __name__ == "__main__":
    build_free_combined()
