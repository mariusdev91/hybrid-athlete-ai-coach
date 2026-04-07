import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  buildCurrentMonthCalendar,
  buildPlanDateIndex,
  getPlanOverview,
} from "../lib/plan-utils.js";
import { api } from "../services/api.js";

function WorkoutPlanPage() {
  const { planId } = useParams();
  const [plan, setPlan] = useState(null);
  const [workoutSessions, setWorkoutSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingSession, setIsSavingSession] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [sessionStatusMessage, setSessionStatusMessage] = useState("");
  const [selectedDateKey, setSelectedDateKey] = useState("");
  const [sessionForm, setSessionForm] = useState(buildDefaultSessionForm());

  const overview = getPlanOverview(plan);
  const dateIndex = useMemo(() => buildPlanDateIndex(plan), [plan]);
  const monthCalendar = useMemo(() => buildCurrentMonthCalendar(plan), [plan]);
  const selectedDay = findDayByKey(monthCalendar.weeks, selectedDateKey);
  const selectedSession = selectedDay?.session || dateIndex[selectedDateKey] || null;
  const sessionLogIndex = buildSessionLogIndex(workoutSessions, dateIndex);
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
    if (!monthCalendar.weeks.length || selectedDateKey) {
      return;
    }

    const todayCell = findDayByKey(monthCalendar.weeks, monthCalendar.todayKey);
    if (todayCell) {
      setSelectedDateKey(todayCell.key);
      return;
    }

    const firstCurrentMonthDay = monthCalendar.weeks.flat().find((day) => day.inCurrentMonth);
    setSelectedDateKey(firstCurrentMonthDay?.key || "");
  }, [monthCalendar, selectedDateKey]);

  useEffect(() => {
    if (!selectedDateKey) {
      return;
    }

    setSessionStatusMessage("");
    setSessionForm(buildDefaultSessionForm());
  }, [selectedDateKey]);

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
      setSessionStatusMessage("Sesiunea a fost logata pentru ziua selectata.");
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
          <h1>Calendarul lunii curente iti arata exact ce ai de facut in fiecare zi.</h1>
          <p className="hero-text">
            Ziua curenta este evidentiata, iar zilele cu sesiuni programate afiseaza un
            preview rapid. Poti selecta orice zi pentru a vedea antrenamentul complet si
            pentru a loga executia.
          </p>
        </div>

        <div className="plan-header-actions">
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
            Download Plan
          </button>
        </div>
      </header>

      {errorMessage ? <div className="banner error">{errorMessage}</div> : null}
      {sessionStatusMessage ? <div className="banner success">{sessionStatusMessage}</div> : null}

      <section className="hero plan-metrics">
        <div className="status-panel">
          <div className="status-grid">
            <article className="status-card">
              <span className="status-label">Current Month</span>
              <strong>{monthCalendar.monthLabel}</strong>
            </article>
            <article className="status-card">
              <span className="status-label">Scheduled Days</span>
              <strong>{monthCalendar.totalScheduledDays}</strong>
            </article>
            <article className="status-card">
              <span className="status-label">Total Sessions</span>
              <strong>{overview.totalSessions}</strong>
            </article>
            <article className="status-card">
              <span className="status-label">Logged Days</span>
              <strong>{loggedDayCount}</strong>
            </article>
          </div>
        </div>
      </section>

      <main className="plan-page-grid month-page-grid">
        <section className="panel">
          <header className="panel-header">
            <h2>{plan?.title || "Monthly Plan Calendar"}</h2>
            <p>{plan?.description || "Plan monthly overview."}</p>
          </header>

          {isLoading ? (
            <div className="placeholder">Loading the monthly calendar...</div>
          ) : (
            <div className="month-calendar">
              <div className="month-weekdays">
                {monthCalendar.weekdayLabels.map((label) => (
                  <span className="month-weekday" key={label}>
                    {label}
                  </span>
                ))}
              </div>

              <div className="month-grid">
                {monthCalendar.weeks.flat().map((day) => {
                  const sessionState = sessionLogIndex[day.key];
                  return (
                    <button
                      className={[
                        "month-day-card",
                        day.inCurrentMonth ? "" : "is-outside",
                        day.isToday ? "is-today" : "",
                        selectedDateKey === day.key ? "is-active" : "",
                        day.session ? "has-session" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      key={day.key}
                      onClick={() => setSelectedDateKey(day.key)}
                      type="button"
                    >
                      <div className="month-day-topline">
                        <span>{day.dayNumber}</span>
                        {day.isToday ? <strong>Today</strong> : null}
                      </div>

                      {day.session ? (
                        <div className="month-day-session">
                          <h4>{day.session.sessionLabel}</h4>
                          <p>{day.session.items.length} exercitii</p>
                          <span className={`session-pill status-${sessionState?.latestStatus || "pending"}`}>
                            {sessionState ? formatSessionStatus(sessionState.latestStatus) : "Planned"}
                          </span>
                        </div>
                      ) : (
                        <div className="month-day-empty">
                          <p>No workout</p>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </section>

        <aside className="panel sticky-panel">
          <header className="panel-header">
            <h2>{selectedDateKey ? formatDateLabel(selectedDateKey) : "Day Detail"}</h2>
            <p>
              Selecteaza o zi din calendar. Daca exista un antrenament programat, il vezi
              aici impreuna cu istoricul si formularul de tracking.
            </p>
          </header>

          {selectedSession ? (
            <div className="stack">
              <div className="summary-card">
                <strong>{selectedSession.sessionLabel}</strong>
                <ul className="plain-list">
                  <li>Data: {selectedSession.isoDate || selectedDateKey}</li>
                  <li>Phase: {selectedSession.phaseName || "n/a"}</li>
                  <li>Focus: {selectedSession.sessionFocus || "n/a"}</li>
                  <li>Exercises: {selectedSession.items.length}</li>
                </ul>
              </div>

              <section className="summary-card">
                <strong>Session Tracking</strong>
                <p className="micro-copy">
                  Logheaza executia, durata si perceptia efortului pentru ziua selectata.
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
                      placeholder="Cum a mers sesiunea? Ai facut ajustari?"
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
                  <div className="placeholder">Nu exista inca nicio sesiune logata pentru aceasta zi.</div>
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
            <div className="placeholder">
              Nu exista antrenament programat pentru ziua selectata. Poti alege o alta zi sau
              poti folosi aceasta vedere ca orientare in calendarul curent.
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

function findDayByKey(weeks, key) {
  for (const week of weeks || []) {
    for (const day of week) {
      if (day.key === key) {
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

function buildSessionLogIndex(workoutSessions = [], dateIndex = {}) {
  const index = {};

  for (const session of workoutSessions) {
    const key = resolveSessionDateKey(session, dateIndex);
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
      latestStatus: session.status || current.latestStatus,
    };
  }

  return index;
}

function resolveSessionDateKey(session, dateIndex) {
  const match = Object.values(dateIndex).find(
    (entry) =>
      entry.weekIndex === (session.week_index || 1) && entry.dayIndex === (session.day_index || 1),
  );
  return match?.isoDate || `${session.week_index || 1}-${session.day_index || 1}`;
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

function formatDateLabel(value) {
  if (!value) {
    return "Day Detail";
  }

  try {
    return new Intl.DateTimeFormat("en-GB", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export default WorkoutPlanPage;
