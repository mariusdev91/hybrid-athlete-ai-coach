import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { buildPlanCalendar, getPlanOverview, getSessionSummary } from "../lib/plan-utils.js";
import { api } from "../services/api.js";

function WorkoutPlanPage() {
  const { planId } = useParams();
  const [plan, setPlan] = useState(null);
  const [workoutSessions, setWorkoutSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingSession, setIsSavingSession] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [sessionStatusMessage, setSessionStatusMessage] = useState("");
  const [selectedSessionKey, setSelectedSessionKey] = useState("");
  const [sessionForm, setSessionForm] = useState(buildDefaultSessionForm());

  const calendar = buildPlanCalendar(plan);
  const overview = getPlanOverview(plan);
  const selectedSession = findSession(calendar, selectedSessionKey);
  const sessionLogIndex = buildSessionLogIndex(workoutSessions);
  const selectedSessionLogs = getLogsForSession(workoutSessions, selectedSession);
  const loggedDayCount = Object.keys(sessionLogIndex).length;

  useEffect(() => {
    let active = true;

    async function loadPlanWorkspace() {
      setIsLoading(true);
      setErrorMessage("");
      setSessionStatusMessage("");

      try {
        const [planPayload, sessionsPayload] = await Promise.all([
          api.getWorkoutPlan(planId),
          api.listWorkoutPlanSessions(planId),
        ]);
        if (!active) {
          return;
        }
        setPlan(planPayload);
        setWorkoutSessions(sessionsPayload);
      } catch (error) {
        if (!active) {
          return;
        }
        setErrorMessage(error.message);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadPlanWorkspace();

    return () => {
      active = false;
    };
  }, [planId]);

  useEffect(() => {
    if (!calendar.length) {
      return;
    }

    if (!selectedSessionKey) {
      setSelectedSessionKey(calendar[0].days[0]?.key || "");
    }
  }, [calendar, selectedSessionKey]);

  useEffect(() => {
    if (!selectedSession) {
      return;
    }

    setSessionStatusMessage("");
    setSessionForm(buildDefaultSessionForm());
  }, [selectedSessionKey, selectedSession]);

  async function handleDownloadWorkbook() {
    if (!plan) {
      return;
    }

    const { downloadPlanWorkbook } = await import("../lib/plan-export.js");
    downloadPlanWorkbook(plan);
  }

  async function handleLogSession(event) {
    event.preventDefault();
    if (!plan || !selectedSession) {
      return;
    }

    setIsSavingSession(true);
    setErrorMessage("");
    setSessionStatusMessage("");

    try {
      await api.createWorkoutSession({
        user_id: plan.user_id,
        workout_plan_id: plan.id,
        week_index: selectedSession.weekIndex,
        day_index: selectedSession.dayIndex,
        session_label: selectedSession.sessionLabel,
        title: selectedSession.sessionLabel,
        status: sessionForm.status,
        duration_minutes: coerceNumber(sessionForm.duration_minutes),
        perceived_exertion: coerceNumber(sessionForm.perceived_exertion),
        notes: sessionForm.notes.trim() || null,
      });

      const sessionsPayload = await api.listWorkoutPlanSessions(plan.id);
      setWorkoutSessions(sessionsPayload);
      setSessionForm((current) => ({
        ...current,
        duration_minutes: "",
        perceived_exertion: "",
        notes: "",
      }));
      setSessionStatusMessage("Session logged for the selected training day.");
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSavingSession(false);
    }
  }

  return (
    <div className="app-shell plan-shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="hero plan-hero">
        <div className="hero-copy">
          <p className="eyebrow">Workout Calendar</p>
          <h1>See the whole cycle, then drill into any training day.</h1>
          <p className="hero-text">
            This page turns the saved plan into a weekly calendar view, with one-click
            detail for each training day, a real session log, and an Excel export split
            into weekly sheets.
          </p>
          <div className="button-row">
            <Link className="secondary-link" to="/">
              Back To Dashboard
            </Link>
            <button
              className="action-button"
              disabled={!plan}
              onClick={() => {
                void handleDownloadWorkbook();
              }}
              type="button"
            >
              Download Excel
            </button>
          </div>
        </div>

        <div className="status-panel">
          {plan ? (
            <div className="status-grid">
              <article className="status-card">
                <span className="status-label">Weeks</span>
                <strong>{overview.totalWeeks}</strong>
              </article>
              <article className="status-card">
                <span className="status-label">Sessions</span>
                <strong>{overview.totalSessions}</strong>
              </article>
              <article className="status-card">
                <span className="status-label">Exercises</span>
                <strong>{overview.totalExercises}</strong>
              </article>
              <article className="status-card">
                <span className="status-label">Logged Days</span>
                <strong>{loggedDayCount}</strong>
              </article>
            </div>
          ) : (
            <div className="placeholder">Plan metrics will appear here once the page loads.</div>
          )}
        </div>
      </header>

      {errorMessage ? <div className="banner error">{errorMessage}</div> : null}
      {sessionStatusMessage ? <div className="banner success">{sessionStatusMessage}</div> : null}

      <main className="plan-page-grid">
        <section className="panel">
          <header className="panel-header">
            <h2>{plan?.title || "Plan Calendar"}</h2>
            <p>{plan?.description || "Saved workout plan overview."}</p>
          </header>

          {isLoading ? (
            <div className="placeholder">Loading the saved plan...</div>
          ) : calendar.length > 0 ? (
            <div className="calendar-week-stack">
              {calendar.map((week) => (
                <article className="week-panel" key={week.weekIndex}>
                  <header className="week-panel-header">
                    <div>
                      <p className="eyebrow">Week {week.weekIndex}</p>
                      <h3>{week.phaseName}</h3>
                    </div>
                    <span className="micro-copy">{week.days.length} training days</span>
                  </header>

                  <div className="calendar-grid">
                    {week.days.map((session) => (
                      <button
                        className={`calendar-day-card ${
                          selectedSessionKey === session.key ? "is-active" : ""
                        }`}
                        key={session.key}
                        onClick={() => setSelectedSessionKey(session.key)}
                        type="button"
                      >
                        <div className="calendar-day-topline">
                          <span>Day {session.dayIndex}</span>
                          <strong>{session.items.length} moves</strong>
                        </div>
                        <h4>{session.sessionLabel}</h4>
                        <p>{session.sessionFocus}</p>
                        <div className="calendar-session-state">
                          {sessionLogIndex[session.key] ? (
                            <>
                              <span
                                className={`session-pill status-${sessionLogIndex[session.key].latestStatus}`}
                              >
                                {formatSessionStatus(sessionLogIndex[session.key].latestStatus)}
                              </span>
                              <span>{sessionLogIndex[session.key].count} logs</span>
                            </>
                          ) : (
                            <span className="session-pill status-pending">Not logged yet</span>
                          )}
                        </div>
                        <div className="calendar-exercise-preview">
                          {session.items.slice(0, 3).map((item) => (
                            <span key={item.id || `${session.key}-${item.sequence_index}`}>
                              {item.exercise_name}
                            </span>
                          ))}
                        </div>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="placeholder">No calendar data available for this plan yet.</div>
          )}
        </section>

        <aside className="panel sticky-panel">
          <header className="panel-header">
            <h2>Day Detail</h2>
            <p>Click one of the training days to inspect the workout content.</p>
          </header>

          {selectedSession ? (
            <div className="stack">
              <div className="summary-card">
                <strong>{selectedSession.sessionLabel}</strong>
                <ul className="plain-list">
                  {getSessionSummary(selectedSession).map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>

              <section className="summary-card">
                <strong>Session Tracking</strong>
                <p className="micro-copy">
                  Log completion, duration, RPE, or notes for this exact training day.
                </p>

                <form className="stack" onSubmit={handleLogSession}>
                  <div className="inline-fields">
                    <label className="field">
                      <span>Status</span>
                      <select
                        onChange={(event) =>
                          setSessionForm((current) => ({
                            ...current,
                            status: event.target.value,
                          }))
                        }
                        value={sessionForm.status}
                      >
                        <option value="completed">Completed</option>
                        <option value="modified">Modified</option>
                        <option value="skipped">Skipped</option>
                      </select>
                    </label>

                    <label className="field">
                      <span>Duration Minutes</span>
                      <input
                        min="0"
                        onChange={(event) =>
                          setSessionForm((current) => ({
                            ...current,
                            duration_minutes: event.target.value,
                          }))
                        }
                        type="number"
                        value={sessionForm.duration_minutes}
                      />
                    </label>
                  </div>

                  <div className="inline-fields">
                    <label className="field">
                      <span>Session RPE</span>
                      <input
                        max="10"
                        min="1"
                        onChange={(event) =>
                          setSessionForm((current) => ({
                            ...current,
                            perceived_exertion: event.target.value,
                          }))
                        }
                        type="number"
                        value={sessionForm.perceived_exertion}
                      />
                    </label>
                  </div>

                  <label className="field">
                    <span>Notes</span>
                    <textarea
                      onChange={(event) =>
                        setSessionForm((current) => ({
                          ...current,
                          notes: event.target.value,
                        }))
                      }
                      placeholder="How did the session feel? Any swaps or pain notes?"
                      rows="4"
                      value={sessionForm.notes}
                    />
                  </label>

                  <div className="button-row">
                    <button className="action-button" disabled={isSavingSession} type="submit">
                      {isSavingSession ? "Saving..." : "Log Session"}
                    </button>
                  </div>
                </form>
              </section>

              <section className="summary-card">
                <strong>Logged History</strong>
                {selectedSessionLogs.length > 0 ? (
                  <div className="session-log-list">
                    {selectedSessionLogs.map((sessionLog) => (
                      <article className="session-log-item" key={sessionLog.id}>
                        <div className="exercise-topline">
                          <strong>{formatSessionStatus(sessionLog.status)}</strong>
                          <span>{formatTimestamp(sessionLog.performed_at)}</span>
                        </div>
                        <p className="micro-copy">
                          Duration {sessionLog.duration_minutes || "-"} min, RPE{" "}
                          {sessionLog.perceived_exertion || "n/a"}.
                        </p>
                        {sessionLog.notes ? <p className="micro-copy">{sessionLog.notes}</p> : null}
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="placeholder">No session has been logged for this day yet.</div>
                )}
              </section>

              {selectedSession.items.map((item) => (
                <article
                  className="exercise-card"
                  key={item.id || `${selectedSession.key}-${item.sequence_index}`}
                >
                  <div className="exercise-topline">
                    <strong>{item.exercise_name}</strong>
                    <span>
                      {item.prescribed_sets || "-"} x {item.prescribed_reps || "-"}
                    </span>
                  </div>
                  <p className="exercise-note">
                    Rest {item.rest_seconds || "-"} sec, target RPE {item.target_rpe || "n/a"}.
                  </p>
                  {item.notes ? <p className="micro-copy">{item.notes}</p> : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="placeholder">Pick a training day to inspect the session.</div>
          )}
        </aside>
      </main>
    </div>
  );
}

function findSession(calendar, sessionKey) {
  for (const week of calendar) {
    for (const day of week.days) {
      if (day.key === sessionKey) {
        return day;
      }
    }
  }

  return null;
}

function buildDefaultSessionForm() {
  return {
    status: "completed",
    duration_minutes: "",
    perceived_exertion: "",
    notes: "",
  };
}

function buildSessionLogIndex(workoutSessions = []) {
  const index = {};

  for (const session of workoutSessions) {
    const key = `${session.week_index || 1}-${session.day_index || 1}`;
    const current = index[key];

    if (!current) {
      index[key] = {
        count: 1,
        latestStatus: session.status || "completed",
      };
      continue;
    }

    index[key] = {
      ...current,
      count: current.count + 1,
    };
  }

  return index;
}

function getLogsForSession(workoutSessions = [], session) {
  if (!session) {
    return [];
  }

  return workoutSessions.filter(
    (item) =>
      (item.week_index || 1) === session.weekIndex && (item.day_index || 1) === session.dayIndex,
  );
}

function coerceNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatSessionStatus(value) {
  if (!value) {
    return "Completed";
  }

  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatTimestamp(value) {
  if (!value) {
    return "Just now";
  }

  try {
    return new Intl.DateTimeFormat("en-GB", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return String(value);
  }
}

export default WorkoutPlanPage;
