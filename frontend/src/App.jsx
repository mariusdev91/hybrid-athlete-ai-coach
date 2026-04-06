import { startTransition, useEffect, useState } from "react";
import { api } from "./services/api.js";

const userDefaults = {
  email: "frontend.demo@example.com",
  full_name: "Frontend Demo Athlete",
  timezone: "Europe/Bucharest",
};

const profileDefaults = {
  primary_sport: "hybrid training",
  experience_level: "intermediate",
  training_days_per_week: 4,
  session_duration_minutes: 50,
  equipment_access: "body only, dumbbell",
  limitations_notes: "Keep overhead volume moderate.",
};

const goalDefaults = {
  title: "Improve performance and conditioning",
  goal_type: "performance",
  priority: 1,
};

const generationDefaults = {
  duration_weeks: 2,
  sessions_per_week: 4,
  focus: "",
  save_plan: true,
};

function App() {
  const [health, setHealth] = useState(null);
  const [statusMessage, setStatusMessage] = useState("Backend status pending.");
  const [errorMessage, setErrorMessage] = useState("");

  const [userForm, setUserForm] = useState(userDefaults);
  const [profileForm, setProfileForm] = useState(profileDefaults);
  const [goalForm, setGoalForm] = useState(goalDefaults);
  const [generationForm, setGenerationForm] = useState(generationDefaults);
  const [searchQuery, setSearchQuery] = useState("glute bridge");

  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [goals, setGoals] = useState([]);
  const [generatedWorkout, setGeneratedWorkout] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadHealth() {
      try {
        const payload = await api.health();
        if (!active) {
          return;
        }
        setHealth(payload);
        setStatusMessage("Backend connection is healthy.");
      } catch (error) {
        if (!active) {
          return;
        }
        setHealth(null);
        setStatusMessage("Backend is not reachable yet.");
        setErrorMessage(error.message);
      }
    }

    loadHealth();

    return () => {
      active = false;
    };
  }, []);

  const steps = [
    { title: "Athlete", value: user ? "Created" : "Pending" },
    { title: "Profile", value: profile ? "Ready" : "Pending" },
    { title: "Goal", value: goals.length > 0 ? `${goals.length} active` : "Pending" },
    { title: "Workout", value: generatedWorkout ? "Generated" : "Pending" },
  ];

  async function handleCreateUser(event) {
    event.preventDefault();
    await runAction(async () => {
      const payload = await api.createUser(userForm);
      setUser(payload);
      setStatusMessage("Athlete created. Next step: save the profile.");
    });
  }

  async function handleCreateProfile(event) {
    event.preventDefault();
    if (!user) {
      setErrorMessage("Create the athlete first.");
      return;
    }

    await runAction(async () => {
      const payload = await api.createProfile({
        user_id: user.id,
        primary_sport: profileForm.primary_sport,
        experience_level: profileForm.experience_level,
        training_days_per_week: Number(profileForm.training_days_per_week),
        session_duration_minutes: Number(profileForm.session_duration_minutes),
        equipment_access: splitList(profileForm.equipment_access),
        limitations_notes: profileForm.limitations_notes,
      });
      setProfile(payload);
      setStatusMessage("Profile saved. You can define a goal now.");
    });
  }

  async function handleCreateGoal(event) {
    event.preventDefault();
    if (!user) {
      setErrorMessage("Create the athlete first.");
      return;
    }

    await runAction(async () => {
      const payload = await api.createGoal({
        user_id: user.id,
        title: goalForm.title,
        goal_type: goalForm.goal_type,
        priority: Number(goalForm.priority),
      });
      setGoals((current) => [payload, ...current]);
      setStatusMessage("Goal saved. The AI coach can now build a starter plan.");
    });
  }

  async function handleGenerateWorkout(event) {
    event.preventDefault();
    if (!user) {
      setErrorMessage("Create the athlete before generating a workout.");
      return;
    }

    await runAction(async () => {
      const payload = await api.generateWorkout(user.id, {
        goal_id: goals[0]?.id,
        duration_weeks: Number(generationForm.duration_weeks),
        sessions_per_week: Number(generationForm.sessions_per_week),
        focus: generationForm.focus || null,
        save_plan: Boolean(generationForm.save_plan),
      });

      startTransition(() => {
        setGeneratedWorkout(payload);
        setSelectedPlan(payload.saved_workout_plan || null);
      });

      setStatusMessage("Starter workout generated successfully.");
    });
  }

  async function handleSearchExercises(event) {
    event.preventDefault();
    if (!searchQuery.trim()) {
      setErrorMessage("Enter a search term for exercises.");
      return;
    }

    setIsSearching(true);
    setErrorMessage("");

    try {
      const payload = await api.searchExercises(searchQuery.trim(), 6);
      startTransition(() => {
        setSearchResults(payload.results || []);
      });
      setStatusMessage(`Search returned ${payload.count} exercise suggestions.`);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSearching(false);
    }
  }

  async function handleReloadSavedPlan() {
    const savedPlanId = generatedWorkout?.saved_workout_plan?.id || selectedPlan?.id;
    if (!savedPlanId) {
      setErrorMessage("There is no saved plan to refresh yet.");
      return;
    }

    await runAction(async () => {
      const payload = await api.getWorkoutPlan(savedPlanId);
      setSelectedPlan(payload);
      setStatusMessage("Saved workout plan refreshed from the backend.");
    });
  }

  async function runAction(action) {
    setIsBusy(true);
    setErrorMessage("");
    try {
      await action();
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Hybrid Athlete AI Coach</p>
          <h1>From athlete setup to a saved starter plan in one screen.</h1>
          <p className="hero-text">
            This frontend bootstraps the current MVP flow on top of the backend we
            already stabilized: athlete, profile, goal, exercise search, AI workout
            generation, and saved plan review.
          </p>
        </div>

        <div className="status-panel">
          <div className="status-topline">
            <span className={`status-dot ${health ? "online" : "offline"}`} />
            <span>{statusMessage}</span>
          </div>
          <div className="status-grid">
            {steps.map((step) => (
              <article className="status-card" key={step.title}>
                <span className="status-label">{step.title}</span>
                <strong>{step.value}</strong>
              </article>
            ))}
          </div>
          <p className="api-note">API base: {api.baseUrl}</p>
        </div>
      </header>

      {errorMessage ? <div className="banner error">{errorMessage}</div> : null}

      <main className="content-grid">
        <section className="column">
          <Panel
            title="1. Athlete Setup"
            subtitle="Create the user record that anchors the rest of the flow."
          >
            <form className="stack" onSubmit={handleCreateUser}>
              <Field
                label="Email"
                value={userForm.email}
                onChange={(value) => setUserForm((current) => ({ ...current, email: value }))}
              />
              <Field
                label="Full name"
                value={userForm.full_name}
                onChange={(value) =>
                  setUserForm((current) => ({ ...current, full_name: value }))
                }
              />
              <Field
                label="Timezone"
                value={userForm.timezone}
                onChange={(value) =>
                  setUserForm((current) => ({ ...current, timezone: value }))
                }
              />
              <button className="action-button" disabled={isBusy}>
                {isBusy ? "Saving..." : "Create Athlete"}
              </button>
            </form>
            {user ? (
              <DataBadge label="User ID" value={user.id} accent="sage" />
            ) : (
              <Placeholder text="No athlete created yet." />
            )}
          </Panel>

          <Panel
            title="2. Athlete Profile"
            subtitle="Capture training context so the AI has constraints to work with."
          >
            <form className="stack" onSubmit={handleCreateProfile}>
              <Field
                label="Primary sport"
                value={profileForm.primary_sport}
                onChange={(value) =>
                  setProfileForm((current) => ({ ...current, primary_sport: value }))
                }
              />
              <Field
                label="Experience level"
                value={profileForm.experience_level}
                onChange={(value) =>
                  setProfileForm((current) => ({ ...current, experience_level: value }))
                }
              />
              <InlineFields>
                <Field
                  label="Days per week"
                  type="number"
                  value={profileForm.training_days_per_week}
                  onChange={(value) =>
                    setProfileForm((current) => ({
                      ...current,
                      training_days_per_week: value,
                    }))
                  }
                />
                <Field
                  label="Session minutes"
                  type="number"
                  value={profileForm.session_duration_minutes}
                  onChange={(value) =>
                    setProfileForm((current) => ({
                      ...current,
                      session_duration_minutes: value,
                    }))
                  }
                />
              </InlineFields>
              <Field
                label="Equipment"
                value={profileForm.equipment_access}
                onChange={(value) =>
                  setProfileForm((current) => ({ ...current, equipment_access: value }))
                }
                hint="Comma separated. Example: body only, dumbbell"
              />
              <Field
                label="Limitations"
                value={profileForm.limitations_notes}
                onChange={(value) =>
                  setProfileForm((current) => ({ ...current, limitations_notes: value }))
                }
              />
              <button className="action-button" disabled={isBusy || !user}>
                {isBusy ? "Saving..." : "Save Profile"}
              </button>
            </form>
            {profile ? (
              <SummaryCard
                title={profile.primary_sport || "Athlete profile"}
                lines={[
                  `Level: ${profile.experience_level || "n/a"}`,
                  `Schedule: ${profile.training_days_per_week || "?"} days x ${
                    profile.session_duration_minutes || "?"
                  } min`,
                  `Equipment: ${(profile.equipment_access || []).join(", ") || "n/a"}`,
                ]}
              />
            ) : (
              <Placeholder text="Profile will appear here after save." />
            )}
          </Panel>

          <Panel title="3. Goal" subtitle="Give the generator a concrete direction.">
            <form className="stack" onSubmit={handleCreateGoal}>
              <Field
                label="Goal title"
                value={goalForm.title}
                onChange={(value) => setGoalForm((current) => ({ ...current, title: value }))}
              />
              <InlineFields>
                <Field
                  label="Goal type"
                  value={goalForm.goal_type}
                  onChange={(value) =>
                    setGoalForm((current) => ({ ...current, goal_type: value }))
                  }
                />
                <Field
                  label="Priority"
                  type="number"
                  value={goalForm.priority}
                  onChange={(value) =>
                    setGoalForm((current) => ({ ...current, priority: value }))
                  }
                />
              </InlineFields>
              <button className="action-button" disabled={isBusy || !user}>
                {isBusy ? "Saving..." : "Save Goal"}
              </button>
            </form>
            {goals.length > 0 ? (
              <div className="goal-list">
                {goals.map((goal) => (
                  <article className="goal-chip" key={goal.id}>
                    <strong>{goal.title}</strong>
                    <span>{goal.goal_type}</span>
                  </article>
                ))}
              </div>
            ) : (
              <Placeholder text="Goals will stack here once created." />
            )}
          </Panel>
        </section>

        <section className="column wide">
          <Panel
            title="4. AI Workout Builder"
            subtitle="Generate a starter plan using the current athlete profile and top goal."
          >
            <form className="stack" onSubmit={handleGenerateWorkout}>
              <InlineFields>
                <Field
                  label="Duration weeks"
                  type="number"
                  value={generationForm.duration_weeks}
                  onChange={(value) =>
                    setGenerationForm((current) => ({
                      ...current,
                      duration_weeks: value,
                    }))
                  }
                />
                <Field
                  label="Sessions per week"
                  type="number"
                  value={generationForm.sessions_per_week}
                  onChange={(value) =>
                    setGenerationForm((current) => ({
                      ...current,
                      sessions_per_week: value,
                    }))
                  }
                />
              </InlineFields>
              <Field
                label="Focus override"
                value={generationForm.focus}
                onChange={(value) =>
                  setGenerationForm((current) => ({ ...current, focus: value }))
                }
                hint="Optional. Leave empty to use the saved goal."
              />
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={generationForm.save_plan}
                  onChange={(event) =>
                    setGenerationForm((current) => ({
                      ...current,
                      save_plan: event.target.checked,
                    }))
                  }
                />
                <span>Persist the generated plan in the backend</span>
              </label>
              <div className="button-row">
                <button className="action-button" disabled={isBusy || !profile}>
                  {isBusy ? "Generating..." : "Generate Starter Plan"}
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={isBusy || !generatedWorkout?.saved_workout_plan}
                  onClick={handleReloadSavedPlan}
                >
                  Refresh Saved Plan
                </button>
              </div>
            </form>

            {generatedWorkout ? (
              <div className="generated-layout">
                <article className="hero-plan">
                  <p className="eyebrow">Generated plan</p>
                  <h2>{generatedWorkout.generated_plan.title}</h2>
                  <p>{generatedWorkout.generated_plan.description}</p>
                  <div className="plan-meta">
                    <DataBadge
                      label="Focus"
                      value={generatedWorkout.generated_plan.focus}
                      accent="sun"
                    />
                    <DataBadge
                      label="Sessions"
                      value={String(generatedWorkout.generated_plan.sessions_per_week)}
                      accent="sky"
                    />
                    <DataBadge
                      label="Weeks"
                      value={String(generatedWorkout.generated_plan.duration_weeks)}
                      accent="sage"
                    />
                  </div>
                </article>

                <article className="context-card">
                  <p className="eyebrow">Generator context</p>
                  <ul className="plain-list">
                    <li>Sport: {generatedWorkout.context.primary_sport || "n/a"}</li>
                    <li>Level: {generatedWorkout.context.experience_level || "n/a"}</li>
                    <li>
                      Equipment:{" "}
                      {generatedWorkout.context.equipment_access.join(", ") || "n/a"}
                    </li>
                    <li>
                      Limitations: {generatedWorkout.context.limitations_notes || "none"}
                    </li>
                  </ul>
                </article>
              </div>
            ) : (
              <Placeholder text="Generate a plan to see the AI output and saved plan preview." />
            )}
          </Panel>

          <Panel
            title="Saved Plan Preview"
            subtitle="What the backend currently persisted for the generated workout."
          >
            {selectedPlan ? (
              <div className="days-grid">
                {groupItemsByDay(selectedPlan.items).map(([day, items]) => (
                  <article className="day-card" key={day}>
                    <header className="day-header">
                      <strong>Day {day}</strong>
                      <span>{items.length} movements</span>
                    </header>
                    <div className="exercise-stack">
                      {items.map((item) => (
                        <article
                          className="exercise-card"
                          key={item.id || `${item.day_index}-${item.sequence_index}`}
                        >
                          <div className="exercise-topline">
                            <strong>{item.exercise_name}</strong>
                            <span>
                              {item.prescribed_sets || "-"} x {item.prescribed_reps || "-"}
                            </span>
                          </div>
                          <p className="exercise-note">
                            Rest {item.rest_seconds || "-"} sec, target RPE{" "}
                            {item.target_rpe || "n/a"}.
                          </p>
                          {item.notes ? <p className="micro-copy">{item.notes}</p> : null}
                        </article>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <Placeholder text="Saved plan details will appear here after generation." />
            )}
          </Panel>

          <Panel
            title="Exercise Search"
            subtitle="Quick semantic lookup against the exercise database."
          >
            <form className="search-row" onSubmit={handleSearchExercises}>
              <input
                className="search-input"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Try: glute bridge, shoulder press, hamstring stretch"
              />
              <button className="secondary-button" disabled={isSearching}>
                {isSearching ? "Searching..." : "Search"}
              </button>
            </form>

            {searchResults.length > 0 ? (
              <div className="search-grid">
                {searchResults.map((result) => (
                  <article className="search-card" key={result.id}>
                    <strong>{result.name}</strong>
                    <p className="micro-copy">
                      {(result.primary_muscles || []).join(", ") || "general"} •{" "}
                      {result.equipment || "no equipment"}
                    </p>
                  </article>
                ))}
              </div>
            ) : (
              <Placeholder text="Search results will render here." />
            )}
          </Panel>
        </section>
      </main>
    </div>
  );
}

function Panel({ title, subtitle, children }) {
  return (
    <section className="panel">
      <header className="panel-header">
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </header>
      {children}
    </section>
  );
}

function Field({ label, hint, type = "text", value, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} />
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

function InlineFields({ children }) {
  return <div className="inline-fields">{children}</div>;
}

function DataBadge({ label, value, accent = "sage" }) {
  return (
    <article className={`data-badge ${accent}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function SummaryCard({ title, lines }) {
  return (
    <article className="summary-card">
      <strong>{title}</strong>
      <ul className="plain-list">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </article>
  );
}

function Placeholder({ text }) {
  return <div className="placeholder">{text}</div>;
}

function splitList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function groupItemsByDay(items = []) {
  const groups = new Map();

  for (const item of items) {
    const dayItems = groups.get(item.day_index) || [];
    dayItems.push(item);
    groups.set(item.day_index, dayItems);
  }

  return Array.from(groups.entries()).sort((left, right) => left[0] - right[0]);
}

export default App;
