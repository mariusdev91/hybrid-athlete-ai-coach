import json

def load_exercises():
    try:
        with open("app/db/exercises.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def semantic_search(query: str):
    # TODO: embeddings + vector DB
    return []
