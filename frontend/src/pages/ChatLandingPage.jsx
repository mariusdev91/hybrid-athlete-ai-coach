import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { buildPlanSessions } from "../lib/plan-utils.js";
import { api } from "../services/api.js";

const PLAN_TRACK_OPTIONS = [
  {
    key: "sport",
    eyebrow: "Sport",
    title: "Basketball si Football",
    description:
      "Pentru sportivi care au nevoie de pozitie, faza de sezon, densitate competitionala si prioritati reale de performanta.",
  },
  {
    key: "training_mode",
    eyebrow: "Training Mode",
    title: "Bodybuilding, CrossFit, Functional, HYROX",
    description:
      "Pentru utilizatori care vor un plan in jurul unui stil de antrenament, nu in jurul unui sport competitiv.",
  },
];

const CONVERSATION_STORAGE_KEY = "hybrid-athlete-conversation-ref-v1";
const DEFAULT_STATUS_MESSAGE = "Alege directia in care vrei sa construim planul.";
const DEFAULT_PROMPT = "Scrie pe scurt ce plan vrei sa obtii.";

function ChatLandingPage() {
  const navigate = useNavigate();
  const transcriptRef = useRef(null);
  const initialConversationId = useMemo(() => loadStoredConversationId(), []);

  const [conversationId, setConversationId] = useState(initialConversationId);
  const [planTrack, setPlanTrack] = useState(null);
  const [messages, setMessages] = useState([]);
  const [preview, setPreview] = useState(null);
  const [draft, setDraft] = useState("");
  const [currentPrompt, setCurrentPrompt] = useState(DEFAULT_PROMPT);
  const [statusMessage, setStatusMessage] = useState(DEFAULT_STATUS_MESSAGE);
  const [errorMessage, setErrorMessage] = useState("");
  const [isConversationLocked, setIsConversationLocked] = useState(false);
  const [isBootstrapping, setIsBootstrapping] = useState(Boolean(initialConversationId));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const previewSessions = useMemo(
    () => buildPlanSessions(preview?.preview_plan).slice(0, 4),
    [preview],
  );

  useEffect(() => {
    if (!initialConversationId) {
      return;
    }

    void hydrateConversation(initialConversationId);
  }, [initialConversationId]);

  useEffect(() => {
    const transcript = transcriptRef.current;
    if (!transcript) {
      return;
    }

    transcript.scrollTop = transcript.scrollHeight;
  }, [messages]);

  async function hydrateConversation(nextConversationId) {
    setIsBootstrapping(true);
    setErrorMessage("");

    try {
      const payload = await api.getConversation(nextConversationId);
      applyConversation(payload);
    } catch (error) {
      clearStoredConversationId();
      resetLocalState();
      setErrorMessage(error.message);
    } finally {
      setIsBootstrapping(false);
    }
  }

  function applyConversation(conversation) {
    persistConversationId(conversation.id);
    setConversationId(conversation.id);
    setPlanTrack(conversation.plan_track);
    setMessages(conversation.messages || []);
    setPreview(conversation.preview || null);
    setCurrentPrompt(conversation.current_prompt || DEFAULT_PROMPT);
    setStatusMessage(conversation.status_message || DEFAULT_STATUS_MESSAGE);
    setIsConversationLocked(Boolean(conversation.is_locked));
    setErrorMessage("");
  }

  function resetLocalState() {
    setConversationId(null);
    setPlanTrack(null);
    setMessages([]);
    setPreview(null);
    setDraft("");
    setCurrentPrompt(DEFAULT_PROMPT);
    setStatusMessage(DEFAULT_STATUS_MESSAGE);
    setIsConversationLocked(false);
  }

  async function handleSelectPlanTrack(nextTrack) {
    setErrorMessage("");
    setDraft("");
    setIsBootstrapping(true);

    try {
      const conversation = await api.createConversation({
        plan_track: nextTrack,
        timezone: getLocalTimezone(),
      });
      applyConversation(conversation);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsBootstrapping(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const answer = draft.trim();
    if (!conversationId || !answer || isSubmitting || isConfirming || isConversationLocked) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const conversation = await api.sendConversationMessage(conversationId, {
        content: answer,
      });
      setDraft("");
      applyConversation(conversation);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleConfirmPlan() {
    if (!conversationId || !preview) {
      return;
    }

    setIsConfirming(true);
    setErrorMessage("");

    try {
      const payload = await api.confirmConversation(conversationId);
      applyConversation(payload.conversation);
      navigate(`/plans/${payload.saved_workout_plan.id}`);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsConfirming(false);
    }
  }

  async function handleResetConversation() {
    if (!planTrack) {
      resetLocalState();
      clearStoredConversationId();
      return;
    }

    setDraft("");
    setErrorMessage("");
    setIsBootstrapping(true);

    try {
      const conversation = await api.createConversation({
        plan_track: planTrack,
        timezone: getLocalTimezone(),
      });
      applyConversation(conversation);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsBootstrapping(false);
    }
  }

  function handleChangePlanTrack() {
    clearStoredConversationId();
    resetLocalState();
  }

  function handleDraftKeyDown(event) {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault();

    if (!draft.trim() || isSubmitting || isConfirming || isConversationLocked) {
      return;
    }

    event.currentTarget.form?.requestSubmit();
  }

  return (
    <div className="app-shell chat-shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="chat-hero">
        <div className="hero-copy">
          <p className="eyebrow">Hybrid Athlete AI Coach</p>
          <h1>
            {planTrack
              ? "O singura conversatie, apoi un plan clar si un calendar real."
              : "Alege mai intai directia, apoi intri in pregatirea planului de antrenament."}
          </h1>
          <p className="hero-text">
            {planTrack
              ? "Convorbirea, intake-ul si preview-ul sunt acum persistate in backend. Tu revii in dashboard, iar coach-ul isi continua starea exact de unde ai ramas."
              : "Pe prima pagina alegi daca intri pe ruta de sport sau pe ruta de training mode. Dupa selectie, coach-ul te conduce prin intake-ul potrivit si iti construieste preview-ul."}
          </p>
        </div>

        <div className="chat-hero-actions">
          {planTrack ? (
            <button className="secondary-button" onClick={handleChangePlanTrack} type="button">
              Change Track
            </button>
          ) : null}
          <Link className="secondary-link" to="/workspace">
            Open Legacy Workspace
          </Link>
          <span className="chat-status">{statusMessage}</span>
        </div>
      </header>

      {errorMessage ? <div className="banner error">{errorMessage}</div> : null}

      {isBootstrapping ? (
        <main className="selector-layout">
          <div className="placeholder">Refac sesiunea conversatiei din backend...</div>
        </main>
      ) : !planTrack ? (
        <main className="selector-layout">
          {PLAN_TRACK_OPTIONS.map((option) => (
            <article className="selector-card" key={option.key}>
              <p className="eyebrow">{option.eyebrow}</p>
              <h2>{option.title}</h2>
              <p>{option.description}</p>
              <button
                className="action-button"
                onClick={() => {
                  void handleSelectPlanTrack(option.key);
                }}
                type="button"
              >
                Intra pe {option.eyebrow}
              </button>
            </article>
          ))}
        </main>
      ) : (
        <main className="chat-layout">
          <section className="chat-panel">
            <div className="chat-transcript" ref={transcriptRef}>
              {messages.map((message) => (
                <article
                  className={`chat-bubble ${message.role === "assistant" ? "assistant" : "user"}`}
                  key={message.id}
                >
                  <span className="chat-role">
                    {message.role === "assistant" ? "Coach" : "Tu"}
                  </span>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>

            {isConversationLocked ? (
              <div className="placeholder">
                Conversatia este inchisa pentru aceasta sesiune. Poti confirma preview-ul
                sau poti folosi Reset ca sa pornesti un intake nou.
                <div className="button-row">
                  <button className="secondary-button" onClick={handleResetConversation} type="button">
                    Reset
                  </button>
                </div>
              </div>
            ) : (
              <form className="chat-input-row" onSubmit={handleSubmit}>
                <label className="field chat-input-field">
                  <span>{currentPrompt}</span>
                  <textarea
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={handleDraftKeyDown}
                    placeholder="Scrie raspunsul tau aici..."
                    rows="3"
                    value={draft}
                  />
                </label>
                <div className="button-row">
                  <button
                    className="action-button"
                    disabled={isSubmitting || isConfirming || !draft.trim()}
                    type="submit"
                  >
                    {isSubmitting ? "Trimitem..." : "Trimite"}
                  </button>
                  <button className="secondary-button" onClick={handleResetConversation} type="button">
                    Reset
                  </button>
                </div>
              </form>
            )}
          </section>

          <aside className="panel preview-panel">
            <header className="panel-header">
              <h2>Plan Preview</h2>
              <p>
                Dupa intake, aici apare structura initiala a planului. Confirmarea
                genereaza planul salvat si te duce direct in calendarul lunar.
              </p>
            </header>

            {preview ? (
              <div className="stack">
                <article className="hero-plan">
                  <p className="eyebrow">Preview Gata</p>
                  <h2>{buildPreviewHeadline(preview)}</h2>
                  <p>{buildPreviewSummary(preview)}</p>
                  <div className="plan-meta">
                    <span className="session-pill status-completed">
                      {formatGoalTypeLabel(preview.preview_goal.goal_type)}
                    </span>
                    <span className="session-pill status-pending">
                      incepe la {preview.preview_plan.start_date}
                    </span>
                  </div>
                </article>

                <div className="badge-grid">
                  <article className="data-badge sage">
                    <span>Weeks</span>
                    <strong>{preview.preview_plan.duration_weeks}</strong>
                  </article>
                  <article className="data-badge sky">
                    <span>Sessions</span>
                    <strong>{preview.preview_plan.sessions_per_week}</strong>
                  </article>
                </div>

                <div className="stack compact">
                  {previewSessions.map((session) => (
                    <article className="summary-card" key={session.key}>
                      <strong>{session.isoDate || `Week ${session.weekIndex} / Day ${session.dayIndex}`}</strong>
                      <ul className="plain-list">
                        <li>{session.sessionLabel}</li>
                        <li>{session.phaseName}</li>
                        <li>{session.items.length} exercitii</li>
                      </ul>
                    </article>
                  ))}
                </div>

                <div className="button-row">
                  <button className="action-button" disabled={isConfirming} onClick={handleConfirmPlan} type="button">
                    {isConfirming ? "Generez..." : "Confirma si Genereaza Planul"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="placeholder">
                Dupa ce alegi track-ul si completezi intake-ul, aici apare preview-ul planului,
                iar starea conversatiei ramane persistata in backend.
              </div>
            )}
          </aside>
        </main>
      )}
    </div>
  );
}

function loadStoredConversationId() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.sessionStorage.getItem(CONVERSATION_STORAGE_KEY);
}

function persistConversationId(conversationId) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(CONVERSATION_STORAGE_KEY, conversationId);
}

function clearStoredConversationId() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(CONVERSATION_STORAGE_KEY);
}

function buildPreviewHeadline(preview) {
  return preview?.preview_plan?.title || "Preview de plan";
}

function buildPreviewSummary(preview) {
  if (!preview) {
    return "";
  }

  const sport = formatSportLabel(preview.context?.primary_sport);
  const goalTitle = preview.preview_goal?.title || "obiectivul tau principal";
  const seasonPhase = formatSeasonPhaseLabel(preview.context?.season_phase);
  const weeks = preview.preview_plan?.duration_weeks || 0;
  const sessions = preview.preview_plan?.sessions_per_week || 0;

  const details = [`${weeks} saptamani`, `${sessions} sesiuni pe saptamana`];

  if (seasonPhase) {
    details.push(`faza: ${seasonPhase}`);
  }

  return `Am pregatit un preview pentru ${sport}, construit in jurul obiectivului "${goalTitle}", cu ${details.join(", ")}.`;
}

function formatGoalTypeLabel(value) {
  const labels = {
    performance: "Performance",
    strength: "Strength",
    endurance: "Endurance",
    "fat loss": "Fat Loss",
    mobility: "Mobility",
    recovery: "Recovery",
  };

  return labels[value] || "Performance";
}

function formatSportLabel(value) {
  const labels = {
    basketball: "basketball",
    football: "football",
    bodybuilding: "bodybuilding",
    crossfit: "crossfit",
    "functional training": "functional training",
    HYROX: "HYROX",
  };

  return labels[value] || "programul tau";
}

function formatSeasonPhaseLabel(value) {
  const labels = {
    off_season: "off-season",
    pre_season: "pre-season",
    in_season: "in-season",
    post_season: "post-season",
  };

  return labels[value] || "";
}

function getLocalTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export default ChatLandingPage;
