import { startTransition, useEffect, useRef, useState } from "react";
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
  const mountedRef = useRef(false);

  const [health, setHealth] = useState(null);
  const [statusMessage, setStatusMessage] = useState("Backend status pending.");
  const [errorMessage, setErrorMessage] = useState("");

  const [userForm, setUserForm] = useState(userDefaults);
  const [profileForm, setProfileForm] = useState(profileDefaults);
  const [goalForm, setGoalForm] = useState(goalDefaults);
  const [generationForm, setGenerationForm] = useState(generationDefaults);
  const [searchQuery, setSearchQuery] = useState("glute bridge");

  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [goals, setGoals] = useState([]);
  const [workoutPlans, setWorkoutPlans] = useState([]);
  const [generatedWorkout, setGeneratedWorkout] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isHydrating, setIsHydrating] = useState(false);
  const [isRefreshingUsers, setIsRefreshingUsers] = useState(false);

  const isWorking = isBusy || isHydrating;

  useEffect(() => {
    mountedRef.current = true;
    void bootstrapApp();

    return () => {
      mountedRef.current = false;
    };
  }, []);

  const steps = [
    { title: "Athlete", value: user ? "Loaded" : "Pending" },
    { title: "Profile", value: profile ? "Ready" : "Missing" },
    { title: "Goal", value: goals.length > 0 ? `${goals.length} active` : "Missing" },
    { title: "Plans", value: workoutPlans.length > 0 ? `${workoutPlans.length} saved` : "None" },
  ];

  async function bootstrapApp() {
    setErrorMessage("");

    try {
      const payload = await api.health();
      if (!mountedRef.current) {
        return;
      }
      setHealth(payload);
      setStatusMessage("Backend connection is healthy.");
    } catch (error) {
      if (!mountedRef.current) {
        return;
      }
      setHealth(null);
      setStatusMessage("Backend is not reachable yet.");
      setErrorMessage(error.message);
      return;
    }

    const roster = await refreshUsers({ silent: true });
    if (!mountedRef.current) {
      return;
    }

    if (roster.length === 0) {
      setStatusMessage("Backend is healthy. Create the first athlete to start the flow.");
      return;
    }

    await loadAthleteWorkspace(roster[0].id, {
      message: `Loaded ${roster[0].full_name} from saved backend data.`,
    });
  }

  async function refreshUsers({ silent = false, preferredUserId = null } = {}) {
    setIsRefreshingUsers(true);

    try {
      const payload = await api.listUsers();
      if (!mountedRef.current) {
        return payload;
      }

      startTransition(() => {
        setUsers(payload);
        setSelectedUserId(
          preferredUserId || selectedUserId || user?.id || payload[0]?.id || "",
        );
      });

      if (!silent) {
        setStatusMessage(
          payload.length > 0
            ? `Roster refreshed. ${payload.length} athlete records available.`
            : "No athlete records saved yet.",
        );
      }

      return payload;
    } catch (error) {
      if (!mountedRef.current) {
        return [];
      }
      setErrorMessage(error.message);
      return [];
    } finally {
      if (mountedRef.current) {
        setIsRefreshingUsers(false);
      }
    }
  }

  async function loadAthleteWorkspace(userId, { message } = {}) {
    if (!userId) {
      setErrorMessage("Select an athlete to load.");
      return;
    }

    setIsHydrating(true);
    setErrorMessage("");

    try {
      const [userRecord, profileRecord, goalsPayload, plansPayload] = await Promise.all([
        api.getUser(userId),
        readProfileIfExists(userId),
        api.listGoals(userId),
        api.listWorkoutPlans(userId),
      ]);

      const latestPlan =
        plansPayload.length > 0 ? await api.getWorkoutPlan(plansPayload[0].id) : null;

      if (!mountedRef.current) {
        return;
      }

      startTransition(() => {
        setUser(userRecord);
        setSelectedUserId(userRecord.id);
        setProfile(profileRecord);
        setGoals(goalsPayload);
        setWorkoutPlans(plansPayload);
        setGeneratedWorkout(null);
        setSelectedPlan(latestPlan);
        setUserForm(mapUserToForm(userRecord));
        setProfileForm(profileRecord ? mapProfileToForm(profileRecord) : profileDefaults);
        setGoalForm(goalsPayload[0] ? mapGoalToForm(goalsPayload[0]) : goalDefaults);
        setGenerationForm(buildGenerationForm(profileRecord));
      });

      setStatusMessage(message || `Loaded athlete workspace for ${userRecord.full_name}.`);
    } catch (error) {
      if (!mountedRef.current) {
        return;
      }
      setErrorMessage(error.message);
    } finally {
      if (mountedRef.current) {
        setIsHydrating(false);
      }
    }
  }

  async function handleCreateUser(event) {
    event.preventDefault();
    setIsBusy(true);
    setErrorMessage("");

    try {
      const payload = await api.createUser(userForm);
      if (!mountedRef.current) {
        return;
      }

      await refreshUsers({ silent: true, preferredUserId: payload.id });
      await loadAthleteWorkspace(payload.id, {
        message: "Athlete created. Next step: save the profile.",
      });
    } catch (error) {
      if (!mountedRef.current) {
        return;
      }

      setErrorMessage(error.message);

      if (error.message.includes("already exists")) {
        const roster = await refreshUsers({ silent: true });
        if (!mountedRef.current) {
          return;
        }

        const match = roster.find(
          (candidate) => candidate.email.toLowerCase() === userForm.email.toLowerCase(),
        );

        if (match) {
          startTransition(() => {
            setSelectedUserId(match.id);
          });
          setStatusMessage("Athlete already exists. Load the saved record from the roster.");
        }
      }
    } finally {
      if (mountedRef.current) {
        setIsBusy(false);
      }
    }
  }

  async function handleLoadSelectedUser(event) {
    event.preventDefault();
    await loadAthleteWorkspace(selectedUserId);
  }

  async function handleCreateProfile(event) {
    event.preventDefault();
    if (!user) {
      setErrorMessage("Create or load the athlete first.");
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

      startTransition(() => {
        setProfile(payload);
        setProfileForm(mapProfileToForm(payload));
        setGenerationForm(buildGenerationForm(payload));
      });

      setStatusMessage("Profile saved. You can define a goal now.");
    });
  }

  async function handleCreateGoal(event) {
    event.preventDefault();
    if (!user) {
      setErrorMessage("Create or load the athlete first.");
      return;
    }

    await runAction(async () => {
      const payload = await api.createGoal({
        user_id: user.id,
        title: goalForm.title,
        goal_type: goalForm.goal_type,
        priority: Number(goalForm.priority),
      });

      startTransition(() => {
        setGoals((current) => [payload, ...current]);
        setGoalForm(mapGoalToForm(payload));
      });

      setStatusMessage("Goal saved. The AI coach can now build a starter plan.");
    });
  }

  async function handleGenerateWorkout(event) {
    event.preventDefault();
    if (!user) {
      setErrorMessage("Create or load the athlete before generating a workout.");
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

      const plansPayload = payload.saved_workout_plan
        ? await api.listWorkoutPlans(user.id)
        : workoutPlans;

      startTransition(() => {
        setGeneratedWorkout(payload);
        setSelectedPlan(payload.saved_workout_plan || null);
        setWorkoutPlans(plansPayload);
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
      if (!mountedRef.current) {
        return;
      }

      startTransition(() => {
        setSearchResults(payload.results || []);
      });

      setStatusMessage(`Search returned ${payload.count} exercise suggestions.`);
    } catch (error) {
      if (mountedRef.current) {
        setErrorMessage(error.message);
      }
    } finally {
      if (mountedRef.current) {
        setIsSearching(false);
      }
    }
  }

  async function handleReloadSavedPlan() {
    const savedPlanId = generatedWorkout?.saved_workout_plan?.id || selectedPlan?.id;
    if (!savedPlanId || !user) {
      setErrorMessage("There is no saved plan to refresh yet.");
      return;
    }

    await runAction(async () => {
      const [planPayload, plansPayload] = await Promise.all([
        api.getWorkoutPlan(savedPlanId),
        api.listWorkoutPlans(user.id),
      ]);

      startTransition(() => {
        setSelectedPlan(planPayload);
        setWorkoutPlans(plansPayload);
      });

      setStatusMessage("Saved workout plan refreshed from the backend.");
    });
  }

  async function handleSelectPlan(planId) {
    await runAction(async () => {
      const payload = await api.getWorkoutPlan(planId);
      setSelectedPlan(payload);
      setStatusMessage("Saved workout plan loaded.");
    });
  }

  async function runAction(action) {
    setIsBusy(true);
    setErrorMessage("");

    try {
      await action();
    } catch (error) {
      if (mountedRef.current) {
        setErrorMessage(error.message);
      }
    } finally {
      if (mountedRef.current) {
        setIsBusy(false);
      }
    }
  }

  return (
    <div className="app-shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Hybrid Athlete AI Coach</p>
          <h1>From saved athlete context to a fresh starter plan in one screen.</h1>
          <p className="hero-text">
            The frontend now reconnects to persisted backend data as well as creating
            new records. You can resume an existing athlete, inspect saved plans, run
            semantic exercise search, and generate a new starter workout without
            losing the flow after refresh.
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
            title="0. Resume Workspace"
            subtitle="Load an athlete already saved in the backend or refresh the roster."
          >
            <form className="stack" onSubmit={handleLoadSelectedUser}>
              <SelectField
                label="Saved athletes"
                value={selectedUserId}
                disabled={users.length === 0 || isWorking}
                onChange={(value) => setSelectedUserId(value)}
                hint={
                  users.length > 0
                    ? `${users.length} athlete records available.`
                    : "Create the first athlete below."
                }
              >
                <option value="">Select an athlete</option>
                {users.map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.full_name} - {candidate.email}
                  </option>
                ))}
              </SelectField>

              <div className="button-row">
                <button
                  className="secondary-button"
                  disabled={!selectedUserId || isWorking}
                  type="submit"
                >
                  {isHydrating ? "Loading..." : "Load Athlete"}
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={isRefreshingUsers}
                  onClick={() => {
                    void refreshUsers();
                  }}
                >
                  {isRefreshingUsers ? "Refreshing..." : "Refresh Roster"}
                </button>
              </div>
            </form>

            {user ? (
              <div className="stack compact">
                <SummaryCard
                  title={user.full_name}
                  lines={[
                    `Email: ${user.email}`,
                    `Timezone: ${user.timezone}`,
                    `Created: ${formatDate(user.created_at)}`,
                  ]}
                />
                <div className="badge-grid">
                  <DataBadge label="Goals" value={String(goals.length)} accent="sage" />
                  <DataBadge
                    label="Saved plans"
                    value={String(workoutPlans.length)}
                    accent="sky"
                  />
                </div>
              </div>
            ) : (
              <Placeholder text="No athlete loaded yet. The most recent saved athlete will load automatically when available." />
            )}
          </Panel>

          <Panel
            title="1. Athlete Setup"
            subtitle="Create a new athlete record when you want a fresh workspace."
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
              <button className="action-button" disabled={isWorking}>
                {isBusy ? "Saving..." : "Create Athlete"}
              </button>
            </form>
            {user ? (
              <DataBadge label="Active user" value={user.id} accent="sage" />
            ) : (
              <Placeholder text="Create or load an athlete to unlock the rest of the flow." />
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
              <button className="action-button" disabled={isWorking || !user}>
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
              <Placeholder text="Profile will appear here after save or when loaded from the backend." />
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
              <button className="action-button" disabled={isWorking || !user}>
                {isBusy ? "Saving..." : "Save Goal"}
              </button>
            </form>
            {goals.length > 0 ? (
              <div className="goal-list">
                {goals.map((goal) => (
                  <article className="goal-chip" key={goal.id}>
                    <strong>{goal.title}</strong>
                    <span>
                      {goal.goal_type} / priority {goal.priority}
                    </span>
                  </article>
                ))}
              </div>
            ) : (
              <Placeholder text="Goals will stack here once created or loaded." />
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
                hint="Optional. Leave empty to use the highest priority saved goal."
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
                <button className="action-button" disabled={isWorking || !profile}>
                  {isBusy ? "Generating..." : "Generate Starter Plan"}
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={isWorking || !generatedWorkout?.saved_workout_plan}
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
                      Goal: {generatedWorkout.goal?.title || generationForm.focus || "general"}
                    </li>
                    <li>
                      Search queries:{" "}
                      {generatedWorkout.search_queries.join(", ") || "none recorded"}
                    </li>
                  </ul>
                </article>
              </div>
            ) : (
              <Placeholder text="Generate a plan to see the AI output and saved plan preview." />
            )}
          </Panel>

          <Panel
            title="Saved Plans"
            subtitle="Switch between plans already stored for the active athlete."
          >
            {workoutPlans.length > 0 ? (
              <div className="plan-list">
                {workoutPlans.map((plan) => (
                  <button
                    className={`plan-list-item ${
                      selectedPlan?.id === plan.id ? "is-active" : ""
                    }`}
                    key={plan.id}
                    onClick={() => {
                      void handleSelectPlan(plan.id);
                    }}
                    type="button"
                  >
                    <strong>{plan.title}</strong>
                    <span>
                      {plan.focus || "general focus"} / {plan.sessions_per_week || "?"} sessions
                    </span>
                    <small>{formatDate(plan.created_at)}</small>
                  </button>
                ))}
              </div>
            ) : (
              <Placeholder text="No saved plans yet for the active athlete." />
            )}
          </Panel>

          <Panel
            title="Saved Plan Preview"
            subtitle="What the backend currently persisted for the selected workout plan."
          >
            {selectedPlan ? (
              <div className="stack">
                <SummaryCard
                  title={selectedPlan.title}
                  lines={[
                    `Focus: ${selectedPlan.focus || "n/a"}`,
                    `Duration: ${selectedPlan.duration_weeks || "?"} weeks`,
                    `Sessions per week: ${selectedPlan.sessions_per_week || "?"}`,
                  ]}
                />

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
              </div>
            ) : (
              <Placeholder text="Saved plan details will appear here after loading or generation." />
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
                      {(result.primary_muscles || []).join(", ") || "general"} /{" "}
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

function SelectField({ label, hint, value, onChange, children, disabled = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select disabled={disabled} value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
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

function mapUserToForm(userRecord) {
  return {
    email: userRecord.email || "",
    full_name: userRecord.full_name || "",
    timezone: userRecord.timezone || "UTC",
  };
}

function mapProfileToForm(profileRecord) {
  return {
    primary_sport: profileRecord.primary_sport || profileDefaults.primary_sport,
    experience_level: profileRecord.experience_level || profileDefaults.experience_level,
    training_days_per_week:
      profileRecord.training_days_per_week || profileDefaults.training_days_per_week,
    session_duration_minutes:
      profileRecord.session_duration_minutes || profileDefaults.session_duration_minutes,
    equipment_access:
      (profileRecord.equipment_access || []).join(", ") || profileDefaults.equipment_access,
    limitations_notes:
      profileRecord.limitations_notes || profileDefaults.limitations_notes,
  };
}

function mapGoalToForm(goalRecord) {
  return {
    title: goalRecord.title || goalDefaults.title,
    goal_type: goalRecord.goal_type || goalDefaults.goal_type,
    priority: goalRecord.priority || goalDefaults.priority,
  };
}

function buildGenerationForm(profileRecord) {
  return {
    ...generationDefaults,
    sessions_per_week:
      profileRecord?.training_days_per_week || generationDefaults.sessions_per_week,
  };
}

async function readProfileIfExists(userId) {
  try {
    return await api.getProfile(userId);
  } catch (error) {
    if (error.message === "Profile not found.") {
      return null;
    }
    throw error;
  }
}

function formatDate(value) {
  if (!value) {
    return "n/a";
  }

  try {
    return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(new Date(value));
  } catch {
    return String(value);
  }
}

export default App;
