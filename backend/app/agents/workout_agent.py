class WorkoutAgent:
    name = "WorkoutAgent"

    def generate_response(self, query, context):
        results = context.get("results", [])
        if not results:
            return "Nu am gasit exercitii pentru a construi un workout."

        names = [result["name"] for result in results[:5]]
        return f"Iata un mini-workout bazat pe cautarea ta: {', '.join(names)}"
