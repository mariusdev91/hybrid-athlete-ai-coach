from app.services.rag_service import load_exercises

exercises = load_exercises()

def search_exercises(query: str):
    query = query.lower()
    return [
        ex for ex in exercises
        if query in ex["name"].lower()
    ]
