import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { buildPlanSessions, slugify } from "../lib/plan-utils.js";
import { api } from "../services/api.js";

const QUESTION_FLOW = [
  { key: "full_name", prompt: "Cum te numesti?", type: "text" },
  { key: "age_years", prompt: "Cati ani ai?", type: "number" },
  { key: "height_cm", prompt: "Ce inaltime ai in centimetri?", type: "number" },
  { key: "weight_kg", prompt: "Ce greutate ai in kilograme?", type: "number" },
  { key: "primary_sport", prompt: "Care este sportul principal sau contextul tau de antrenament?", type: "text" },
  { key: "experience_level", prompt: "Ce nivel ai acum: beginner, intermediate sau advanced?", type: "text" },
  { key: "training_days_per_week", prompt: "Cate zile pe saptamana poti aloca pentru antrenament?", type: "number" },
  { key: "session_duration_minutes", prompt: "Cat dureaza in mod realist o sedinta pentru tine, in minute?", type: "number" },
  { key: "equipment_access", prompt: "Ce echipament ai disponibil? Scrie liber, de exemplu: body only, dumbbell, barbell.", type: "list" },
  { key: "goal_title", prompt: "Care este obiectivul tau principal in urmatoarele 4-8 saptamani?", type: "text" },
  { key: "goal_type", prompt: "Cum ai incadra obiectivul: performance, strength, endurance, fat loss, mobility sau recovery?", type: "text" },
  { key: "limitations_notes", prompt: "Ai limitari, accidentari sau miscari pe care vrei sa le evitam? Daca nu, scrie nu.", type: "optional" },
];

const CHAT_SESSION_STORAGE_KEY = "hybrid-athlete-chat-session-v1";
const DEFAULT_STATUS_MESSAGE = "Coach-ul este gata pentru intake.";

function ChatLandingPage() {
  const navigate = useNavigate();
  const initialState = useMemo(() => loadStoredChatState(), []);
  const [messages, setMessages] = useState(initialState.messages);
  const [draft, setDraft] = useState(initialState.draft);
  const [stepIndex, setStepIndex] = useState(initialState.stepIndex);
  const [intake, setIntake] = useState(initialState.intake);
  const [preview, setPreview] = useState(initialState.preview);
  const [statusMessage, setStatusMessage] = useState(initialState.statusMessage);
  const [errorMessage, setErrorMessage] = useState(initialState.errorMessage);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const isConversationLocked = stepIndex >= QUESTION_FLOW.length;

  const previewSessions = useMemo(
    () => buildPlanSessions(preview?.preview_plan).slice(0, 4),
    [preview],
  );

  useEffect(() => {
    persistChatState({
      messages,
      draft,
      stepIndex,
      intake,
      preview,
      statusMessage,
      errorMessage,
    });
  }, [draft, errorMessage, intake, messages, preview, statusMessage, stepIndex]);

  async function handleSubmit(event) {
    event.preventDefault();
    const answer = draft.trim();
    if (!answer || isPreviewing || isConfirming || isConversationLocked) {
      return;
    }

    setDraft("");
    setErrorMessage("");
    appendMessage("user", answer);

    if (stepIndex === -1) {
      const nextIntake = {
        ...intake,
        request_text: answer,
        goal_title: intake.goal_title || answer,
      };
      setIntake(nextIntake);
      setStepIndex(0);
      appendMessage(
        "assistant",
        `Am inteles directia generala. Ca sa-ti structurez corect preview-ul, am nevoie de cateva detalii. ${QUESTION_FLOW[0].prompt}`,
      );
      setStatusMessage("Intake-ul a inceput. Raspunde natural, un mesaj pe rand.");
      return;
    }

    if (stepIndex >= QUESTION_FLOW.length) {
      appendMessage(
        "assistant",
        "Preview-ul este deja pregatit. Daca vrei un alt intake, foloseste Reset; daca directia este buna, confirma planul.",
      );
      return;
    }

    const question = QUESTION_FLOW[stepIndex];
    const parsed = parseAnswer(question, answer);
    if (!parsed.ok) {
      appendMessage("assistant", parsed.error);
      return;
    }

    const nextIntake = {
      ...intake,
      [question.key]: parsed.value,
    };
    setIntake(nextIntake);

    if (stepIndex < QUESTION_FLOW.length - 1) {
      const nextStep = stepIndex + 1;
      setStepIndex(nextStep);
      appendMessage("assistant", QUESTION_FLOW[nextStep].prompt);
      return;
    }

    await buildPreview(nextIntake);
  }

  async function buildPreview(nextIntake) {
    setIsPreviewing(true);
    setPreview(null);
    setStatusMessage("Construiesc preview-ul planului de antrenament...");

    try {
      const payload = await api.previewPlan({
        ...nextIntake,
        goal_title: nextIntake.goal_title || nextIntake.request_text,
        goal_type: normalizeGoalType(nextIntake.goal_type),
      });
      setPreview(payload);
      setStepIndex(QUESTION_FLOW.length);
      setStatusMessage("Preview-ul este gata. Daca iti place directia, il poti confirma.");
      appendMessage(
        "assistant",
        "Am construit un preview periodizat. Verifica sumarul de mai jos, iar daca directia este buna, confirma si iti generez planul complet.",
      );
    } catch (error) {
      setErrorMessage(error.message);
      appendMessage("assistant", "Nu am reusit sa construiesc preview-ul. Hai sa mai incercam dupa ce verifici raspunsurile.");
    } finally {
      setIsPreviewing(false);
    }
  }

  async function handleConfirmPlan() {
    if (!preview) {
      return;
    }

    setIsConfirming(true);
    setErrorMessage("");
    setStatusMessage("Persist datele si generez planul final...");

    try {
      const fullName = intake.full_name || "Hybrid Athlete";
      const timestamp = Date.now();
      const user = await api.createUser({
        email: `${slugify(fullName)}.${timestamp}@local.hybrid-athlete`,
        full_name: fullName,
        timezone: intake.timezone || getLocalTimezone(),
      });

      await api.saveProfile(user.id, {
        age_years: intake.age_years,
        height_cm: intake.height_cm,
        weight_kg: intake.weight_kg,
        primary_sport: intake.primary_sport,
        experience_level: intake.experience_level,
        training_days_per_week: intake.training_days_per_week,
        session_duration_minutes: intake.session_duration_minutes,
        equipment_access: intake.equipment_access,
        limitations_notes: intake.limitations_notes || null,
      });

      const goal = await api.createGoal({
        user_id: user.id,
        title: intake.goal_title || intake.request_text,
        goal_type: normalizeGoalType(intake.goal_type),
        priority: 1,
      });

      const generated = await api.generateWorkout(user.id, {
        goal_id: goal.id,
        duration_weeks: preview.preview_plan.duration_weeks,
        sessions_per_week: intake.training_days_per_week,
        start_date: intake.start_date,
        equipment_access: intake.equipment_access,
        limitations_notes: intake.limitations_notes || null,
        save_plan: true,
      });

      if (!generated.saved_workout_plan?.id) {
        throw new Error("Planul a fost generat, dar nu a fost salvat corect.");
      }

      navigate(`/plans/${generated.saved_workout_plan.id}`);
    } catch (error) {
      setErrorMessage(error.message);
      setStatusMessage("A aparut o problema la confirmarea planului.");
    } finally {
      setIsConfirming(false);
    }
  }

  function handleResetConversation() {
    const resetState = createDefaultChatState();
    clearStoredChatState();
    setMessages(resetState.messages);
    setDraft("");
    setStepIndex(resetState.stepIndex);
    setIntake(resetState.intake);
    setPreview(null);
    setStatusMessage("Coach-ul este gata pentru un nou intake.");
    setErrorMessage("");
  }

  function appendMessage(role, content) {
    setMessages((current) => [
      ...current,
      {
        id: `${role}-${current.length + 1}-${Date.now()}`,
        role,
        content,
      },
    ]);
  }

  const currentPrompt =
    stepIndex >= 0 && stepIndex < QUESTION_FLOW.length
      ? QUESTION_FLOW[stepIndex].prompt
      : "Scrie pe scurt ce plan vrei sa obtii.";

  return (
    <div className="app-shell chat-shell">
      <div className="backdrop backdrop-a" />
      <div className="backdrop backdrop-b" />

      <header className="chat-hero">
        <div className="hero-copy">
          <p className="eyebrow">Hybrid Athlete AI Coach</p>
          <h1>O singura conversatie, apoi un plan clar si un calendar real.</h1>
          <p className="hero-text">
            In loc de formulare clasice, landing page-ul devine un intake ghidat.
            Tu descrii obiectivul, orchestratorul cere contextul lipsa, apoi iti
            construieste un preview de plan inainte de confirmare.
          </p>
        </div>

        <div className="chat-hero-actions">
          <Link className="secondary-link" to="/workspace">
            Open Legacy Workspace
          </Link>
          <span className="chat-status">{statusMessage}</span>
        </div>
      </header>

      {errorMessage ? <div className="banner error">{errorMessage}</div> : null}

      <main className="chat-layout">
        <section className="chat-panel">
          <div className="chat-transcript">
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
                  placeholder="Scrie raspunsul tau aici..."
                  rows="3"
                  value={draft}
                />
              </label>
              <div className="button-row">
                <button
                  className="action-button"
                  disabled={isPreviewing || isConfirming || !draft.trim()}
                  type="submit"
                >
                  {isPreviewing ? "Construiesc..." : "Trimite"}
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
                <p className="eyebrow">Preview Ready</p>
                <h2>{preview.preview_plan.title}</h2>
                <p>{preview.preview_plan.description}</p>
                <div className="plan-meta">
                  <span className="session-pill status-completed">
                    {preview.preview_goal.goal_type}
                  </span>
                  <span className="session-pill status-pending">
                    starts {preview.preview_plan.start_date}
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
              Conversatia iti va construi aici un preview de plan, fara sa persiste
              date in backend pana nu confirmi.
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

function parseAnswer(question, value) {
  if (question.type === "number") {
    const parsed = Number(value.replace(",", "."));
    if (!Number.isFinite(parsed) || parsed <= 0) {
      return { ok: false, error: `Am nevoie de o valoare numerica valida. ${question.prompt}` };
    }
    return { ok: true, value: parsed };
  }

  if (question.type === "list") {
    const parsed = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    if (parsed.length === 0) {
      return {
        ok: false,
        error: `Am nevoie de cel putin un element de echipament sau de raspunsul "body only". ${question.prompt}`,
      };
    }
    return { ok: true, value: parsed };
  }

  if (question.type === "optional") {
    const normalized = value.trim().toLowerCase();
    if (!normalized || ["nu", "none", "nimic", "n/a"].includes(normalized)) {
      return { ok: true, value: "" };
    }
    return { ok: true, value: value.trim() };
  }

  if (!value.trim()) {
    return { ok: false, error: `Am nevoie de un raspuns mai clar. ${question.prompt}` };
  }

  return { ok: true, value: value.trim() };
}

function normalizeGoalType(value) {
  const normalized = String(value || "performance").trim().toLowerCase();
  if (!normalized) {
    return "performance";
  }
  return normalized;
}

function loadStoredChatState() {
  const defaultState = createDefaultChatState();
  if (typeof window === "undefined") {
    return defaultState;
  }

  try {
    const raw = window.sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY);
    if (!raw) {
      return defaultState;
    }

    const stored = JSON.parse(raw);
    return {
      messages:
        Array.isArray(stored.messages) && stored.messages.length > 0
          ? stored.messages
          : defaultState.messages,
      draft: typeof stored.draft === "string" ? stored.draft : "",
      stepIndex: Number.isInteger(stored.stepIndex) ? stored.stepIndex : defaultState.stepIndex,
      intake:
        stored.intake && typeof stored.intake === "object"
          ? { ...defaultState.intake, ...stored.intake }
          : defaultState.intake,
      preview: stored.preview || null,
      statusMessage:
        typeof stored.statusMessage === "string" && stored.statusMessage.trim()
          ? stored.statusMessage
          : defaultState.statusMessage,
      errorMessage: typeof stored.errorMessage === "string" ? stored.errorMessage : "",
    };
  } catch {
    return defaultState;
  }
}

function persistChatState(state) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(CHAT_SESSION_STORAGE_KEY, JSON.stringify(state));
}

function clearStoredChatState() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(CHAT_SESSION_STORAGE_KEY);
}

function createDefaultChatState() {
  return {
    messages: [createWelcomeMessage()],
    draft: "",
    stepIndex: -1,
    intake: buildDefaultIntake(),
    preview: null,
    statusMessage: DEFAULT_STATUS_MESSAGE,
    errorMessage: "",
  };
}

function buildDefaultIntake() {
  return {
    request_text: "",
    full_name: "",
    age_years: null,
    height_cm: null,
    weight_kg: null,
    primary_sport: "",
    experience_level: "",
    training_days_per_week: 4,
    session_duration_minutes: 60,
    equipment_access: [],
    goal_title: "",
    goal_type: "performance",
    limitations_notes: "",
    duration_weeks: 4,
    start_date: getTodayIso(),
    timezone: getLocalTimezone(),
  };
}

function createWelcomeMessage() {
  return {
    id: "welcome",
    role: "assistant",
    content:
      "Spune-mi pe scurt ce vrei sa obtii, iar eu iti construiesc intake-ul pas cu pas si iti pregatesc un preview de plan.",
  };
}

function getTodayIso() {
  const today = new Date();
  return new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function getLocalTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export default ChatLandingPage;
