const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null
        ? payload.detail || JSON.stringify(payload)
        : payload;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return payload;
}

export const api = {
  baseUrl: API_BASE_URL,
  health() {
    return request("/db/health");
  },
  searchExercises(query, k = 6) {
    const params = new URLSearchParams({ q: query, k: String(k) });
    return request(`/exercises/search?${params.toString()}`);
  },
  listUsers() {
    return request("/db/users");
  },
  getUser(userId) {
    return request(`/db/users/${userId}`);
  },
  createUser(payload) {
    return request("/db/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  createProfile(payload) {
    return request("/db/profiles", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getProfile(userId) {
    return request(`/db/users/${userId}/profile`);
  },
  createGoal(payload) {
    return request("/db/goals", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listGoals(userId) {
    return request(`/db/users/${userId}/goals`);
  },
  generateWorkout(userId, payload) {
    return request(`/ai/users/${userId}/generate-workout`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listWorkoutPlans(userId) {
    return request(`/db/users/${userId}/workout-plans`);
  },
  getWorkoutPlan(planId) {
    return request(`/db/workout-plans/${planId}`);
  },
};
