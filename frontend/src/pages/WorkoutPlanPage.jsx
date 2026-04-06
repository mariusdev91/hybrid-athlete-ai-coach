import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { buildPlanCalendar, getPlanOverview, getSessionSummary } from "../lib/plan-utils.js";
import { api } from "../services/api.js";

function WorkoutPlanPage() {
  const { planId } = useParams();
  const [plan, setPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedSessionKey, setSelectedSessionKey] = useState("");

  const calendar = buildPlanCalendar(plan);
  const overview = getPlanOverview(plan);
  const selectedSession = findSession(calendar, selectedSessionKey);

  useEffect(() => {
    let active = true;

    async function loadPlan() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const payload = await api.getWorkoutPlan(planId);
        if (!active) {
          return;
        }
        setPlan(payload);
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

    void loadPlan();

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

  async function handleDownloadWorkbook() {
    if (!plan) {
      return;
    }

    const { downloadPlanWorkbook } = await import("../lib/plan-export.js");
    downloadPlanWorkbook(plan);
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
            detail for each training day and an Excel export split into weekly sheets.
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
                <span className="status-label">Plan Status</span>
                <strong>{plan.status}</strong>
              </article>
            </div>
          ) : (
            <div className="placeholder">Plan metrics will appear here once the page loads.</div>
          )}
        </div>
      </header>

      {errorMessage ? <div className="banner error">{errorMessage}</div> : null}

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

export default WorkoutPlanPage;
