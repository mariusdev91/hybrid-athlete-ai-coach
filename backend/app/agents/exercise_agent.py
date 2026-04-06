class ExerciseAgent:
    name = "ExerciseAgent"

    def generate_response(self, query, context):
        results = context.get("results", [])
        if not results:
            return "Nu am gasit exercitii relevante."

        names = [result["name"] for result in results]
        return f"Exercitii recomandate: {', '.join(names)}"
