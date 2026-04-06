class WorkoutAgent:
    name = "WorkoutAgent"

    def generate_response(self, query, context):
        results = context.get("results", [])
        if not results:
            return "Nu am găsit exerciții pentru a construi un workout."

        names = [r["name"] for r in results[:5]]
        return f"Iată un mini-workout bazat pe căutarea ta: {', '.join(names)}"
