class ExerciseAgent:
    name = "ExerciseAgent"

    def generate_response(self, query, context):
        results = context.get("results", [])
        if not results:
            return "Nu am găsit exerciții relevante."

        names = [r["name"] for r in results]
        return f"Exerciții recomandate: {', '.join(names)}"
