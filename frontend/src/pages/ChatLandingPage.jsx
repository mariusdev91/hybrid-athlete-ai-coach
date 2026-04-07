import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { buildPlanSessions, slugify } from "../lib/plan-utils.js";
import { api } from "../services/api.js";

const SPORT_QUESTION_FLOW = [
  { key: "full_name", prompt: "Cum te numesti?", type: "text" },
  { key: "age_years", prompt: "Cati ani ai?", type: "number" },
  { key: "height_cm", prompt: "Ce inaltime ai in centimetri?", type: "number" },
  { key: "weight_kg", prompt: "Ce greutate ai in kilograme?", type: "number" },
  { key: "primary_sport", prompt: "Pentru ce sport construim planul: basketball sau football?", type: "text" },
  { key: "sport_position", prompt: "Care este pozitia sau rolul sportivului?", type: "text" },
  { key: "season_phase", prompt: "In ce faza esti: off_season, pre_season, in_season sau post_season?", type: "text" },
  { key: "weekly_competitions", prompt: "Cate competitii sau meciuri ai intr-o saptamana obisnuita?", type: "number" },
  { key: "experience_level", prompt: "Ce nivel ai acum: beginner, intermediate sau advanced?", type: "text" },
  { key: "training_days_per_week", prompt: "Cate zile pe saptamana poti aloca pentru antrenament?", type: "number" },
  { key: "session_duration_minutes", prompt: "Cat dureaza in mod realist o sedinta pentru tine, in minute?", type: "number" },
  { key: "equipment_access", prompt: "Ce echipament ai disponibil? Scrie liber, de exemplu: body only, dumbbell, barbell.", type: "list" },
  { key: "performance_priorities", prompt: "Care sunt prioritatile cheie? Exemplu: acceleration, change of direction, vertical power.", type: "list" },
  { key: "goal_title", prompt: "Care este obiectivul tau principal in urmatoarele 4-8 saptamani?", type: "text" },
  { key: "goal_type", prompt: "Cum ai incadra obiectivul: performance, strength, endurance, fat loss, mobility sau recovery?", type: "text" },
  { key: "limitations_notes", prompt: "Ai limitari, accidentari sau miscari pe care vrei sa le evitam? Daca nu, scrie nu.", type: "optional" },
];

const TRAINING_MODE_QUESTION_FLOW = [
  { key: "full_name", prompt: "Cum te numesti?", type: "text" },
  { key: "age_years", prompt: "Cati ani ai?", type: "number" },
  { key: "height_cm", prompt: "Ce inaltime ai in centimetri?", type: "number" },
  { key: "weight_kg", prompt: "Ce greutate ai in kilograme?", type: "number" },
  { key: "training_mode", prompt: "Ce tip de pregatire vrei: bodybuilding, crossfit, functional training sau HYROX?", type: "text" },
  { key: "experience_level", prompt: "Ce nivel ai acum: beginner, intermediate sau advanced?", type: "text" },
  { key: "training_days_per_week", prompt: "Cate zile pe saptamana poti aloca pentru antrenament?", type: "number" },
  { key: "session_duration_minutes", prompt: "Cat dureaza in mod realist o sedinta pentru tine, in minute?", type: "number" },
  { key: "equipment_access", prompt: "Ce echipament ai disponibil? Scrie liber, de exemplu: body only, dumbbell, barbell.", type: "list" },
  { key: "goal_title", prompt: "Care este obiectivul tau principal in urmatoarele 4-8 saptamani?", type: "text" },
  { key: "goal_type", prompt: "Cum ai incadra obiectivul: performance, strength, endurance, fat loss, mobility sau recovery?", type: "text" },
  { key: "limitations_notes", prompt: "Ai limitari, accidentari sau miscari pe care vrei sa le evitam? Daca nu, scrie nu.", type: "optional" },
];

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

const CHAT_SESSION_STORAGE_KEY = "hybrid-athlete-chat-session-v2";
const DEFAULT_STATUS_MESSAGE = "Alege directia in care vrei sa construim planul.";
const LOW_SIGNAL_ANSWERS = new Set([
  "cel de mai sus",
  "cea de mai sus",
  "cele de mai sus",
  "de mai sus",
  "mai sus",
  "acelasi",
  "aceeasi",
  "idem",
  "same as above",
  "as above",
  "above",
]);

function ChatLandingPage() {
  const navigate = useNavigate();
  const transcriptRef = useRef(null);
  const initialState = useMemo(() => loadStoredChatState(), []);
  const [planTrack, setPlanTrack] = useState(initialState.planTrack);
  const [messages, setMessages] = useState(initialState.messages);
  const [draft, setDraft] = useState(initialState.draft);
  const [stepIndex, setStepIndex] = useState(initialState.stepIndex);
  const [intake, setIntake] = useState(initialState.intake);
  const [preview, setPreview] = useState(initialState.preview);
  const [statusMessage, setStatusMessage] = useState(initialState.statusMessage);
  const [errorMessage, setErrorMessage] = useState(initialState.errorMessage);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const questionFlow = useMemo(() => getQuestionFlow(planTrack), [planTrack]);
  const isConversationLocked = Boolean(planTrack) && stepIndex >= questionFlow.length && questionFlow.length > 0;

  const previewSessions = useMemo(
    () => buildPlanSessions(preview?.preview_plan).slice(0, 4),
    [preview],
  );

  useEffect(() => {
    persistChatState({
      planTrack,
      messages,
      draft,
      stepIndex,
      intake,
      preview,
      statusMessage,
      errorMessage,
    });
  }, [draft, errorMessage, intake, messages, planTrack, preview, statusMessage, stepIndex]);

  useEffect(() => {
    const transcript = transcriptRef.current;
    if (!transcript) {
      return;
    }

    transcript.scrollTop = transcript.scrollHeight;
  }, [messages]);

  async function handleSubmit(event) {
    event.preventDefault();
    const answer = draft.trim();
    if (!planTrack || !answer || isPreviewing || isConfirming || isConversationLocked) {
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
        `Am inteles directia generala. Ca sa-ti structurez corect preview-ul, am nevoie de cateva detalii. ${questionFlow[0].prompt}`,
      );
      setStatusMessage(getTrackActiveMessage(planTrack));
      return;
    }

    if (stepIndex >= questionFlow.length) {
      appendMessage(
        "assistant",
        "Preview-ul este deja pregatit. Daca vrei un alt intake, foloseste Reset; daca directia este buna, confirma planul.",
      );
      return;
    }

    const question = questionFlow[stepIndex];
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

    if (stepIndex < questionFlow.length - 1) {
      const nextStep = stepIndex + 1;
      setStepIndex(nextStep);
      appendMessage("assistant", questionFlow[nextStep].prompt);
      return;
    }

    await buildPreview(nextIntake);
  }

  async function buildPreview(nextIntake) {
    setIsPreviewing(true);
    setPreview(null);
    setStatusMessage("Construiesc preview-ul planului de antrenament...");

    try {
      const payload = await api.previewPlan(buildPreviewPayload(planTrack, nextIntake));
      setPreview(payload);
      setStepIndex(questionFlow.length);
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

      await api.saveProfile(user.id, buildProfilePayload(planTrack, intake));

      const goal = await api.createGoal({
        user_id: user.id,
        title: intake.goal_title || intake.request_text,
        goal_type: normalizeGoalType(intake.goal_type),
        priority: 1,
      });

      const generated = await api.generateWorkout(user.id, {
        ...buildGenerationPayload(planTrack, intake),
        goal_id: goal.id,
        duration_weeks: preview.preview_plan.duration_weeks,
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
    const resetState = createDefaultChatState(planTrack);
    clearStoredChatState();
    setPlanTrack(resetState.planTrack);
    setMessages(resetState.messages);
    setDraft("");
    setStepIndex(resetState.stepIndex);
    setIntake(resetState.intake);
    setPreview(null);
    setStatusMessage(planTrack ? getTrackReadyMessage(planTrack) : DEFAULT_STATUS_MESSAGE);
    setErrorMessage("");
  }

  function handleSelectPlanTrack(nextTrack) {
    const nextState = createDefaultChatState(nextTrack);
    clearStoredChatState();
    setPlanTrack(nextTrack);
    setMessages(nextState.messages);
    setDraft(nextState.draft);
    setStepIndex(nextState.stepIndex);
    setIntake(nextState.intake);
    setPreview(nextState.preview);
    setStatusMessage(nextState.statusMessage);
    setErrorMessage("");
  }

  function handleChangePlanTrack() {
    const nextState = createDefaultChatState(null);
    clearStoredChatState();
    setPlanTrack(null);
    setMessages(nextState.messages);
    setDraft(nextState.draft);
    setStepIndex(nextState.stepIndex);
    setIntake(nextState.intake);
    setPreview(nextState.preview);
    setStatusMessage(nextState.statusMessage);
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
    stepIndex >= 0 && stepIndex < questionFlow.length
      ? questionFlow[stepIndex].prompt
      : "Scrie pe scurt ce plan vrei sa obtii.";

  function handleDraftKeyDown(event) {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault();

    if (!draft.trim() || isPreviewing || isConfirming || isConversationLocked) {
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
              ? "In loc de formulare clasice, landing page-ul devine un intake ghidat. Tu descrii obiectivul, orchestratorul cere contextul lipsa, apoi iti construieste un preview de plan inainte de confirmare."
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

      {!planTrack ? (
        <main className="selector-layout">
          {PLAN_TRACK_OPTIONS.map((option) => (
            <article className="selector-card" key={option.key}>
              <p className="eyebrow">{option.eyebrow}</p>
              <h2>{option.title}</h2>
              <p>{option.description}</p>
              <button
                className="action-button"
                onClick={() => handleSelectPlanTrack(option.key)}
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
                fara sa persiste date in backend pana nu confirmi.
              </div>
            )}
          </aside>
        </main>
      )}
    </div>
  );
}

function parseAnswer(question, value) {
  const trimmedValue = value.trim();

  if (question.type === "number") {
    const parsed = Number(value.replace(",", "."));
    const minimum = question.key === "weekly_competitions" ? 0 : 1;
    if (!Number.isFinite(parsed) || parsed < minimum) {
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
    const normalized = trimmedValue.toLowerCase();
    if (!normalized || ["nu", "none", "nimic", "n/a"].includes(normalized)) {
      return { ok: true, value: "" };
    }
    return { ok: true, value: trimmedValue };
  }

  if (!trimmedValue) {
    return { ok: false, error: `Am nevoie de un raspuns mai clar. ${question.prompt}` };
  }

  if (question.key === "goal_title" && isLowSignalAnswer(trimmedValue)) {
    return {
      ok: false,
      error: "Am nevoie de un obiectiv scris concret, nu de un raspuns de tip 'cel de mai sus'. Spune clar ce vrei sa obtii in 4-8 saptamani.",
    };
  }

  if (question.key === "primary_sport") {
    const normalizedSport = normalizePrimarySport(trimmedValue);
    if (!normalizedSport) {
      return {
        ok: false,
        error: "Pentru sport, alege una dintre optiunile recunoscute: basketball sau football.",
      };
    }
    return { ok: true, value: normalizedSport };
  }

  if (question.key === "training_mode") {
    const normalizedTrainingMode = normalizeTrainingMode(trimmedValue);
    if (!normalizedTrainingMode) {
      return {
        ok: false,
        error: "Pentru training mode, alege una dintre optiunile: bodybuilding, crossfit, functional training sau hyrox.",
      };
    }
    return { ok: true, value: normalizedTrainingMode };
  }

  if (question.key === "season_phase") {
    const normalizedSeasonPhase = normalizeSeasonPhase(trimmedValue);
    if (!normalizedSeasonPhase) {
      return {
        ok: false,
        error: "Faza de sezon trebuie sa fie una dintre: off_season, pre_season, in_season sau post_season.",
      };
    }
    return { ok: true, value: normalizedSeasonPhase };
  }

  if (question.key === "experience_level") {
    const normalizedExperienceLevel = normalizeExperienceLevel(trimmedValue);
    if (!normalizedExperienceLevel) {
      return {
        ok: false,
        error: "Nivelul trebuie sa fie beginner, intermediate sau advanced.",
      };
    }
    return { ok: true, value: normalizedExperienceLevel };
  }

  if (question.key === "goal_type") {
    const normalizedGoalType = normalizeGoalType(trimmedValue);
    if (!normalizedGoalType) {
      return {
        ok: false,
        error: "Goal type trebuie sa fie unul singur: performance, strength, endurance, fat loss, mobility sau recovery.",
      };
    }
    return { ok: true, value: normalizedGoalType };
  }

  return { ok: true, value: trimmedValue };
}

function normalizeGoalType(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) {
    return "performance";
  }

  if (normalized.includes("performance") || normalized.includes("performanta")) {
    return "performance";
  }
  if (normalized.includes("strength") || normalized.includes("forta")) {
    return "strength";
  }
  if (
    normalized.includes("endurance") ||
    normalized.includes("conditioning") ||
    normalized.includes("rezistenta") ||
    normalized.includes("cardio")
  ) {
    return "endurance";
  }
  if (
    normalized.includes("fat loss") ||
    normalized.includes("weight loss") ||
    normalized.includes("slabire")
  ) {
    return "fat loss";
  }
  if (normalized.includes("mobility") || normalized.includes("mobilitate")) {
    return "mobility";
  }
  if (
    normalized.includes("recovery") ||
    normalized.includes("recuperare") ||
    normalized.includes("restore")
  ) {
    return "recovery";
  }

  return null;
}

function getQuestionFlow(planTrack) {
  if (planTrack === "sport") {
    return SPORT_QUESTION_FLOW;
  }
  if (planTrack === "training_mode") {
    return TRAINING_MODE_QUESTION_FLOW;
  }
  return [];
}

function getTrackReadyMessage(planTrack) {
  if (planTrack === "sport") {
    return "Modul Sport este gata. Spune-mi pe scurt ce fel de sportiv pregatim.";
  }
  if (planTrack === "training_mode") {
    return "Modul Training Mode este gata. Spune-mi ce stil de pregatire vrei sa construim.";
  }
  return DEFAULT_STATUS_MESSAGE;
}

function getTrackActiveMessage(planTrack) {
  if (planTrack === "sport") {
    return "Intake-ul sport-specific a inceput. Raspunde natural, un mesaj pe rand.";
  }
  if (planTrack === "training_mode") {
    return "Intake-ul pentru training mode a inceput. Raspunde natural, un mesaj pe rand.";
  }
  return DEFAULT_STATUS_MESSAGE;
}

function buildPreviewPayload(planTrack, intake) {
  return {
    request_text: intake.request_text,
    full_name: intake.full_name,
    age_years: intake.age_years,
    height_cm: intake.height_cm,
    weight_kg: intake.weight_kg,
    primary_sport: resolvePrimarySport(planTrack, intake),
    sport_position: planTrack === "sport" ? intake.sport_position || null : null,
    season_phase: planTrack === "sport" ? normalizeSeasonPhase(intake.season_phase) : null,
    weekly_competitions: planTrack === "sport" ? intake.weekly_competitions : null,
    experience_level: intake.experience_level,
    training_days_per_week: intake.training_days_per_week,
    session_duration_minutes: intake.session_duration_minutes,
    equipment_access: intake.equipment_access,
    performance_priorities: planTrack === "sport" ? intake.performance_priorities : [],
    limitations_notes: intake.limitations_notes || null,
    goal_title: intake.goal_title || intake.request_text,
    goal_type: normalizeGoalType(intake.goal_type),
    duration_weeks: intake.duration_weeks,
    start_date: intake.start_date,
    timezone: intake.timezone,
  };
}

function buildProfilePayload(planTrack, intake) {
  return {
    age_years: intake.age_years,
    height_cm: intake.height_cm,
    weight_kg: intake.weight_kg,
    primary_sport: resolvePrimarySport(planTrack, intake),
    sport_position: planTrack === "sport" ? intake.sport_position || null : null,
    season_phase: planTrack === "sport" ? normalizeSeasonPhase(intake.season_phase) : null,
    weekly_competitions: planTrack === "sport" ? intake.weekly_competitions : null,
    experience_level: intake.experience_level,
    training_days_per_week: intake.training_days_per_week,
    session_duration_minutes: intake.session_duration_minutes,
    equipment_access: intake.equipment_access,
    performance_priorities: planTrack === "sport" ? intake.performance_priorities : [],
    limitations_notes: intake.limitations_notes || null,
  };
}

function buildGenerationPayload(planTrack, intake) {
  return {
    sessions_per_week: intake.training_days_per_week,
    start_date: intake.start_date,
    equipment_access: intake.equipment_access,
    limitations_notes: intake.limitations_notes || null,
    sport_position: planTrack === "sport" ? intake.sport_position || null : null,
    season_phase: planTrack === "sport" ? normalizeSeasonPhase(intake.season_phase) : null,
    weekly_competitions: planTrack === "sport" ? intake.weekly_competitions : null,
    performance_priorities: planTrack === "sport" ? intake.performance_priorities : [],
  };
}

function resolvePrimarySport(planTrack, intake) {
  if (planTrack === "sport") {
    return normalizePrimarySport(intake.primary_sport) || "basketball";
  }

  const trainingMode = String(intake.training_mode || "").trim();
  return trainingMode || "hybrid training";
}

function normalizeSeasonPhase(value) {
  if (!value) {
    return null;
  }

  const normalized = String(value).trim().toLowerCase();
  const aliases = {
    offseason: "off_season",
    "off season": "off_season",
    off_season: "off_season",
    extrasezon: "off_season",
    preseason: "pre_season",
    "pre season": "pre_season",
    pre_season: "pre_season",
    presezon: "pre_season",
    inseason: "in_season",
    "in season": "in_season",
    in_season: "in_season",
    sezon: "in_season",
    postseason: "post_season",
    "post season": "post_season",
    post_season: "post_season",
    postsezon: "post_season",
  };

  return aliases[normalized] || null;
}

function loadStoredChatState() {
  const defaultState = createDefaultChatState(null);
  if (typeof window === "undefined") {
    return defaultState;
  }

  try {
    const raw = window.sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY);
    if (!raw) {
      return defaultState;
    }

    const stored = JSON.parse(raw);
    const planTrack = stored.planTrack === "sport" || stored.planTrack === "training_mode"
      ? stored.planTrack
      : null;
    const trackDefaultState = createDefaultChatState(planTrack);

    return {
      planTrack,
      messages:
        Array.isArray(stored.messages) && stored.messages.length > 0
          ? stored.messages
          : trackDefaultState.messages,
      draft: typeof stored.draft === "string" ? stored.draft : "",
      stepIndex: Number.isInteger(stored.stepIndex) ? stored.stepIndex : trackDefaultState.stepIndex,
      intake:
        stored.intake && typeof stored.intake === "object"
          ? { ...trackDefaultState.intake, ...stored.intake }
          : trackDefaultState.intake,
      preview: stored.preview || null,
      statusMessage:
        typeof stored.statusMessage === "string" && stored.statusMessage.trim()
          ? stored.statusMessage
          : trackDefaultState.statusMessage,
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

function createDefaultChatState(planTrack = null) {
  return {
    planTrack,
    messages: planTrack ? [createWelcomeMessage(planTrack)] : [],
    draft: "",
    stepIndex: -1,
    intake: buildDefaultIntake(planTrack),
    preview: null,
    statusMessage: planTrack ? getTrackReadyMessage(planTrack) : DEFAULT_STATUS_MESSAGE,
    errorMessage: "",
  };
}

function buildDefaultIntake(planTrack = null) {
  return {
    plan_track: planTrack,
    request_text: "",
    full_name: "",
    age_years: null,
    height_cm: null,
    weight_kg: null,
    primary_sport: "",
    sport_position: "",
    season_phase: "",
    weekly_competitions: null,
    experience_level: "",
    training_days_per_week: 4,
    session_duration_minutes: 60,
    equipment_access: [],
    performance_priorities: [],
    training_mode: "",
    goal_title: "",
    goal_type: "performance",
    limitations_notes: "",
    duration_weeks: 4,
    start_date: getTodayIso(),
    timezone: getLocalTimezone(),
  };
}

function createWelcomeMessage(planTrack) {
  if (planTrack === "sport") {
    return {
      id: "welcome",
      role: "assistant",
      content:
        "Ai intrat pe modulul Sport. Spune-mi pe scurt ce sportiv pregatim si ce vrei sa obtii, iar eu iti construiesc intake-ul sport-specific pas cu pas.",
    };
  }

  return {
    id: "welcome",
    role: "assistant",
    content:
      "Ai intrat pe modulul Training Mode. Spune-mi ce tip de pregatire vrei sa construim, iar eu iti pregatesc intake-ul si preview-ul de plan.",
  };
}

function isLowSignalAnswer(value) {
  return LOW_SIGNAL_ANSWERS.has(String(value || "").trim().toLowerCase());
}

function normalizePrimarySport(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const aliases = {
    basketball: "basketball",
    baschet: "basketball",
    football: "football",
    soccer: "football",
    fotbal: "football",
  };

  return aliases[normalized] || null;
}

function normalizeTrainingMode(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const aliases = {
    bodybuilding: "bodybuilding",
    crossfit: "crossfit",
    "cross-fit": "crossfit",
    "functional training": "functional training",
    functional: "functional training",
    hyrox: "HYROX",
  };

  return aliases[normalized] || null;
}

function normalizeExperienceLevel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const aliases = {
    beginner: "beginner",
    incepator: "beginner",
    intermediate: "intermediate",
    mediu: "intermediate",
    advanced: "advanced",
    avansat: "advanced",
  };

  return aliases[normalized] || null;
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

  const details = [
    `${weeks} saptamani`,
    `${sessions} sesiuni pe saptamana`,
  ];

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
