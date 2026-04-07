from __future__ import annotations

import re
from datetime import UTC
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.db_rel.models import AthleteProfile
from app.db_rel.models import Conversation
from app.db_rel.models import ConversationMessage
from app.db_rel.models import Goal
from app.db_rel.models import User
from app.schemas.ai import ConversationConfirmResponse
from app.schemas.ai import ConversationCreateRequest
from app.schemas.ai import ConversationIntakeState
from app.schemas.ai import ConversationMessageCreate
from app.schemas.ai import ConversationMessageRead
from app.schemas.ai import ConversationRead
from app.schemas.ai import WorkoutGenerationRequest
from app.schemas.ai import WorkoutPlanPreviewRequest
from app.schemas.ai import WorkoutPlanPreviewResponse
from app.schemas.database import GoalRead
from app.schemas.database import UserRead
from app.schemas.database import WorkoutPlanDetailRead
from app.services.intake_normalization import is_low_signal_answer
from app.services.intake_normalization import normalize_goal_type
from app.services.intake_normalization import normalize_primary_sport
from app.services.intake_normalization import normalize_season_phase
from app.services.intake_normalization import sanitize_goal_title
from app.services.plan_preview_service import build_preview_response
from app.services.workout_generator import workout_generator
from app.utils.normalizer import normalize_text


SPORT_QUESTION_FLOW = (
    {"key": "full_name", "prompt": "Cum te numesti?", "type": "text"},
    {"key": "age_years", "prompt": "Cati ani ai?", "type": "number"},
    {"key": "height_cm", "prompt": "Ce inaltime ai in centimetri?", "type": "number"},
    {"key": "weight_kg", "prompt": "Ce greutate ai in kilograme?", "type": "number"},
    {
        "key": "primary_sport",
        "prompt": "Pentru ce sport construim planul: basketball sau football?",
        "type": "text",
    },
    {"key": "sport_position", "prompt": "Care este pozitia sau rolul sportivului?", "type": "text"},
    {
        "key": "season_phase",
        "prompt": "In ce faza esti: off_season, pre_season, in_season sau post_season?",
        "type": "text",
    },
    {
        "key": "weekly_competitions",
        "prompt": "Cate competitii sau meciuri ai intr-o saptamana obisnuita?",
        "type": "number",
    },
    {
        "key": "experience_level",
        "prompt": "Ce nivel ai acum: beginner, intermediate sau advanced?",
        "type": "text",
    },
    {
        "key": "training_days_per_week",
        "prompt": "Cate zile pe saptamana poti aloca pentru antrenament?",
        "type": "number",
    },
    {
        "key": "session_duration_minutes",
        "prompt": "Cat dureaza in mod realist o sedinta pentru tine, in minute?",
        "type": "number",
    },
    {
        "key": "equipment_access",
        "prompt": "Ce echipament ai disponibil? Scrie liber, de exemplu: body only, dumbbell, barbell.",
        "type": "list",
    },
    {
        "key": "performance_priorities",
        "prompt": "Care sunt prioritatile cheie? Exemplu: acceleration, change of direction, vertical power.",
        "type": "list",
    },
    {
        "key": "goal_title",
        "prompt": "Care este obiectivul tau principal in urmatoarele 4-8 saptamani?",
        "type": "text",
    },
    {
        "key": "goal_type",
        "prompt": "Cum ai incadra obiectivul: performance, strength, endurance, fat loss, mobility sau recovery?",
        "type": "text",
    },
    {
        "key": "limitations_notes",
        "prompt": "Ai limitari, accidentari sau miscari pe care vrei sa le evitam? Daca nu, scrie nu.",
        "type": "optional",
    },
)


TRAINING_MODE_QUESTION_FLOW = (
    {"key": "full_name", "prompt": "Cum te numesti?", "type": "text"},
    {"key": "age_years", "prompt": "Cati ani ai?", "type": "number"},
    {"key": "height_cm", "prompt": "Ce inaltime ai in centimetri?", "type": "number"},
    {"key": "weight_kg", "prompt": "Ce greutate ai in kilograme?", "type": "number"},
    {
        "key": "training_mode",
        "prompt": "Ce tip de pregatire vrei: bodybuilding, crossfit, functional training sau HYROX?",
        "type": "text",
    },
    {
        "key": "experience_level",
        "prompt": "Ce nivel ai acum: beginner, intermediate sau advanced?",
        "type": "text",
    },
    {
        "key": "training_days_per_week",
        "prompt": "Cate zile pe saptamana poti aloca pentru antrenament?",
        "type": "number",
    },
    {
        "key": "session_duration_minutes",
        "prompt": "Cat dureaza in mod realist o sedinta pentru tine, in minute?",
        "type": "number",
    },
    {
        "key": "equipment_access",
        "prompt": "Ce echipament ai disponibil? Scrie liber, de exemplu: body only, dumbbell, barbell.",
        "type": "list",
    },
    {
        "key": "goal_title",
        "prompt": "Care este obiectivul tau principal in urmatoarele 4-8 saptamani?",
        "type": "text",
    },
    {
        "key": "goal_type",
        "prompt": "Cum ai incadra obiectivul: performance, strength, endurance, fat loss, mobility sau recovery?",
        "type": "text",
    },
    {
        "key": "limitations_notes",
        "prompt": "Ai limitari, accidentari sau miscari pe care vrei sa le evitam? Daca nu, scrie nu.",
        "type": "optional",
    },
)


TRAINING_MODE_ALIASES = {
    "bodybuilding": "bodybuilding",
    "crossfit": "crossfit",
    "cross-fit": "crossfit",
    "functional training": "functional training",
    "functional": "functional training",
    "hyrox": "HYROX",
}


EXPERIENCE_LEVEL_ALIASES = {
    "beginner": "beginner",
    "incepator": "beginner",
    "intermediate": "intermediate",
    "mediu": "intermediate",
    "advanced": "advanced",
    "avansat": "advanced",
}


DEFAULT_STATUS_MESSAGE = "Alege directia in care vrei sa construim planul."


class ConversationService:
    def create_conversation(
        self,
        db: Session,
        payload: ConversationCreateRequest,
    ) -> ConversationRead:
        intake = build_default_intake(payload.plan_track, payload.timezone)
        conversation = Conversation(
            plan_track=payload.plan_track,
            status="collecting",
            timezone=payload.timezone,
            current_step_index=-1,
            intake_data=intake.model_dump(mode="json"),
            preview_data=None,
        )
        db.add(conversation)
        db.flush()
        self._append_message(conversation, "assistant", create_welcome_message(payload.plan_track))
        db.commit()
        return self.get_conversation(db, conversation.id)

    def get_conversation(self, db: Session, conversation_id: str) -> ConversationRead:
        conversation = self._load_conversation(db, conversation_id)
        return self._serialize(conversation)

    def submit_message(
        self,
        db: Session,
        conversation_id: str,
        payload: ConversationMessageCreate,
    ) -> ConversationRead:
        conversation = self._load_conversation(db, conversation_id)
        answer = payload.content.strip()
        if not answer:
            raise HTTPException(status_code=400, detail="Message content cannot be empty.")

        if conversation.status != "collecting":
            raise HTTPException(
                status_code=409,
                detail="Conversation is already locked. Reset the flow to start again.",
            )

        self._append_message(conversation, "user", answer)
        intake = ConversationIntakeState.model_validate(conversation.intake_data or {})
        flow = get_question_flow(conversation.plan_track)

        if conversation.current_step_index == -1:
            intake.request_text = answer
            if not intake.goal_title:
                intake.goal_title = answer
            conversation.intake_data = intake.model_dump(mode="json")
            conversation.current_step_index = 0
            self._append_message(
                conversation,
                "assistant",
                "Am inteles directia generala. Ca sa-ti structurez corect preview-ul, am nevoie de cateva detalii. "
                f"{flow[0]['prompt']}",
            )
            db.commit()
            return self.get_conversation(db, conversation.id)

        question = flow[conversation.current_step_index]
        parsed = parse_answer(question, answer)
        if not parsed["ok"]:
            self._append_message(conversation, "assistant", parsed["error"])
            db.commit()
            return self.get_conversation(db, conversation.id)

        setattr(intake, question["key"], parsed["value"])
        conversation.intake_data = intake.model_dump(mode="json")

        if conversation.current_step_index < len(flow) - 1:
            conversation.current_step_index += 1
            self._append_message(conversation, "assistant", flow[conversation.current_step_index]["prompt"])
            db.commit()
            return self.get_conversation(db, conversation.id)

        preview_payload = build_preview_payload(conversation.plan_track, intake)
        preview = build_preview_response(preview_payload)
        conversation.preview_data = preview.model_dump(mode="json")
        conversation.current_step_index = len(flow)
        conversation.status = "preview_ready"
        self._append_message(
            conversation,
            "assistant",
            "Am construit un preview periodizat. Verifica sumarul de mai jos, iar daca directia este buna, confirma si iti generez planul complet.",
        )
        db.commit()
        return self.get_conversation(db, conversation.id)

    def confirm_conversation(self, db: Session, conversation_id: str) -> ConversationConfirmResponse:
        conversation = self._load_conversation(db, conversation_id)
        if conversation.status == "confirmed":
            raise HTTPException(status_code=409, detail="Conversation was already confirmed.")
        if conversation.status != "preview_ready" or not conversation.preview_data:
            raise HTTPException(status_code=400, detail="Conversation preview is not ready yet.")

        intake = ConversationIntakeState.model_validate(conversation.intake_data or {})
        preview = WorkoutPlanPreviewResponse.model_validate(conversation.preview_data)
        full_name = intake.full_name.strip() or "Hybrid Athlete"

        user = User(
            email=build_local_email(full_name, conversation.id),
            full_name=full_name,
            timezone=intake.timezone or conversation.timezone or "UTC",
        )
        db.add(user)
        db.flush()

        profile = AthleteProfile(
            user_id=user.id,
            age_years=intake.age_years,
            gender=intake.gender or None,
            height_cm=intake.height_cm,
            weight_kg=intake.weight_kg,
            primary_sport=resolve_primary_sport(conversation.plan_track, intake),
            sport_position=(intake.sport_position or None) if conversation.plan_track == "sport" else None,
            season_phase=normalize_season_phase(intake.season_phase) if conversation.plan_track == "sport" else None,
            weekly_competitions=intake.weekly_competitions if conversation.plan_track == "sport" else None,
            experience_level=intake.experience_level or None,
            training_days_per_week=intake.training_days_per_week,
            session_duration_minutes=intake.session_duration_minutes,
            equipment_access=intake.equipment_access,
            performance_priorities=intake.performance_priorities if conversation.plan_track == "sport" else [],
            limitations_notes=intake.limitations_notes or None,
        )
        goal = Goal(
            user_id=user.id,
            title=sanitize_goal_title(
                intake.goal_title,
                fallback_text=intake.request_text,
                primary_sport=resolve_primary_sport(conversation.plan_track, intake),
                goal_type=intake.goal_type,
            ),
            goal_type=normalize_goal_type(intake.goal_type),
            priority=1,
            status="active",
        )
        db.add(profile)
        db.add(goal)
        db.flush()

        generation_request = build_generation_request(conversation.plan_track, intake, preview)
        generated_plan, context, search_queries = workout_generator.generate_plan(
            user_id=user.id,
            request=generation_request,
            profile=profile,
            goal=goal,
        )
        saved_model = workout_generator.save_plan(
            db=db,
            user_id=user.id,
            goal_id=goal.id,
            plan=generated_plan,
        )

        conversation.user_id = user.id
        conversation.confirmed_workout_plan_id = saved_model.id
        conversation.status = "confirmed"
        self._append_message(
            conversation,
            "assistant",
            "Planul a fost confirmat si salvat. Poti deschide calendarul complet si reveni oricand la aceasta conversatie.",
        )
        db.commit()

        return ConversationConfirmResponse(
            conversation=self.get_conversation(db, conversation.id),
            user=UserRead.model_validate(user),
            goal=GoalRead.model_validate(goal),
            saved_workout_plan=WorkoutPlanDetailRead.model_validate(saved_model),
            generated_plan=generated_plan,
            context=context,
            search_queries=search_queries,
        )

    def _load_conversation(self, db: Session, conversation_id: str) -> Conversation:
        conversation = (
            db.query(Conversation)
            .options(selectinload(Conversation.messages))
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return conversation

    def _serialize(self, conversation: Conversation) -> ConversationRead:
        intake = ConversationIntakeState.model_validate(conversation.intake_data or {})
        preview = (
            WorkoutPlanPreviewResponse.model_validate(conversation.preview_data)
            if conversation.preview_data
            else None
        )
        flow = get_question_flow(conversation.plan_track)
        is_locked = conversation.status in {"preview_ready", "confirmed"} or conversation.current_step_index >= len(flow)
        current_prompt = get_current_prompt(
            conversation.plan_track,
            conversation.status,
            conversation.current_step_index,
        )
        messages = [ConversationMessageRead.model_validate(message) for message in conversation.messages]
        return ConversationRead(
            id=conversation.id,
            user_id=conversation.user_id,
            confirmed_workout_plan_id=conversation.confirmed_workout_plan_id,
            plan_track=conversation.plan_track,
            status=conversation.status,
            timezone=conversation.timezone,
            current_step_index=conversation.current_step_index,
            current_prompt=current_prompt,
            status_message=get_status_message(
                conversation.plan_track,
                conversation.status,
                conversation.current_step_index,
            ),
            is_locked=is_locked,
            intake=intake,
            preview=preview,
            messages=messages,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    def _append_message(self, conversation: Conversation, role: str, content: str) -> None:
        conversation.messages.append(
            ConversationMessage(
                role=role,
                content=content,
                sequence_index=len(conversation.messages) + 1,
            )
        )


def get_question_flow(plan_track: str) -> tuple[dict[str, str], ...]:
    if plan_track == "sport":
        return SPORT_QUESTION_FLOW
    if plan_track == "training_mode":
        return TRAINING_MODE_QUESTION_FLOW
    raise HTTPException(status_code=400, detail="Unsupported plan track.")


def build_default_intake(plan_track: str, timezone: str) -> ConversationIntakeState:
    return ConversationIntakeState(
        plan_track=plan_track,
        start_date=datetime.now(UTC).date(),
        timezone=timezone or "UTC",
    )


def create_welcome_message(plan_track: str) -> str:
    if plan_track == "sport":
        return (
            "Ai intrat pe modulul Sport. Spune-mi pe scurt ce sportiv pregatim si ce vrei sa obtii, "
            "iar eu iti construiesc intake-ul sport-specific pas cu pas."
        )
    return (
        "Ai intrat pe modulul Training Mode. Spune-mi ce tip de pregatire vrei sa construim, "
        "iar eu iti pregatesc intake-ul si preview-ul de plan."
    )


def get_track_ready_message(plan_track: str) -> str:
    if plan_track == "sport":
        return "Modul Sport este gata. Spune-mi pe scurt ce fel de sportiv pregatim."
    if plan_track == "training_mode":
        return "Modul Training Mode este gata. Spune-mi ce stil de pregatire vrei sa construim."
    return DEFAULT_STATUS_MESSAGE


def get_track_active_message(plan_track: str) -> str:
    if plan_track == "sport":
        return "Intake-ul sport-specific a inceput. Raspunde natural, un mesaj pe rand."
    if plan_track == "training_mode":
        return "Intake-ul pentru training mode a inceput. Raspunde natural, un mesaj pe rand."
    return DEFAULT_STATUS_MESSAGE


def get_status_message(plan_track: str, status: str, step_index: int) -> str:
    if status == "confirmed":
        return "Planul este deja confirmat si salvat. Poti reveni oricand sau poti porni un intake nou."
    if status == "preview_ready":
        return "Preview-ul este gata. Daca iti place directia, il poti confirma."
    if step_index == -1:
        return get_track_ready_message(plan_track)
    return get_track_active_message(plan_track)


def get_current_prompt(plan_track: str, status: str, step_index: int) -> str | None:
    if status != "collecting":
        return None
    flow = get_question_flow(plan_track)
    if 0 <= step_index < len(flow):
        return flow[step_index]["prompt"]
    return "Scrie pe scurt ce plan vrei sa obtii."


def parse_answer(question: dict[str, str], value: str) -> dict[str, object]:
    trimmed_value = value.strip()

    if question["type"] == "number":
        normalized_value = value.replace(",", ".")
        try:
            parsed = float(normalized_value)
        except ValueError:
            parsed = None

        minimum = 0 if question["key"] == "weekly_competitions" else 1
        if parsed is None or parsed < minimum:
            return {"ok": False, "error": f"Am nevoie de o valoare numerica valida. {question['prompt']}"}

        number_value = int(parsed) if parsed.is_integer() else parsed
        return {"ok": True, "value": number_value}

    if question["type"] == "list":
        parsed = [item.strip() for item in value.split(",") if item.strip()]
        if not parsed:
            return {
                "ok": False,
                "error": f"Am nevoie de cel putin un raspuns clar, separat prin virgula. {question['prompt']}",
            }
        return {"ok": True, "value": parsed}

    if question["type"] == "optional":
        normalized = normalize_text(trimmed_value)
        if not normalized or normalized in {"nu", "none", "nimic", "n/a"}:
            return {"ok": True, "value": ""}
        return {"ok": True, "value": trimmed_value}

    if not trimmed_value:
        return {"ok": False, "error": f"Am nevoie de un raspuns mai clar. {question['prompt']}"}

    if question["key"] == "goal_title" and is_low_signal_answer(trimmed_value):
        return {
            "ok": False,
            "error": "Am nevoie de un obiectiv scris concret, nu de un raspuns de tip 'cel de mai sus'. Spune clar ce vrei sa obtii in 4-8 saptamani.",
        }

    if question["key"] == "primary_sport":
        normalized_sport = normalize_primary_sport(trimmed_value)
        if not normalized_sport or normalized_sport not in {"basketball", "football"}:
            return {
                "ok": False,
                "error": "Pentru sport, alege una dintre optiunile recunoscute: basketball sau football.",
            }
        return {"ok": True, "value": normalized_sport}

    if question["key"] == "training_mode":
        normalized_training_mode = normalize_training_mode(trimmed_value)
        if not normalized_training_mode:
            return {
                "ok": False,
                "error": "Pentru training mode, alege una dintre optiunile: bodybuilding, crossfit, functional training sau HYROX.",
            }
        return {"ok": True, "value": normalized_training_mode}

    if question["key"] == "season_phase":
        normalized_phase = normalize_season_phase(trimmed_value)
        if normalized_phase not in {"off_season", "pre_season", "in_season", "post_season"}:
            return {
                "ok": False,
                "error": "Faza de sezon trebuie sa fie una dintre: off_season, pre_season, in_season sau post_season.",
            }
        return {"ok": True, "value": normalized_phase}

    if question["key"] == "experience_level":
        normalized_level = normalize_experience_level(trimmed_value)
        if not normalized_level:
            return {
                "ok": False,
                "error": "Nivelul trebuie sa fie beginner, intermediate sau advanced.",
            }
        return {"ok": True, "value": normalized_level}

    if question["key"] == "goal_type":
        normalized_goal = normalize_goal_type(trimmed_value)
        return {"ok": True, "value": normalized_goal}

    return {"ok": True, "value": trimmed_value}


def normalize_training_mode(value: str | None) -> str | None:
    normalized = normalize_text(value or "")
    return TRAINING_MODE_ALIASES.get(normalized)


def normalize_experience_level(value: str | None) -> str | None:
    normalized = normalize_text(value or "")
    return EXPERIENCE_LEVEL_ALIASES.get(normalized)


def resolve_primary_sport(plan_track: str, intake: ConversationIntakeState) -> str:
    if plan_track == "sport":
        return normalize_primary_sport(intake.primary_sport) or "basketball"
    return intake.training_mode.strip() or "hybrid training"


def build_preview_payload(
    plan_track: str,
    intake: ConversationIntakeState,
) -> WorkoutPlanPreviewRequest:
    return WorkoutPlanPreviewRequest(
        request_text=intake.request_text,
        full_name=intake.full_name or None,
        age_years=intake.age_years,
        gender=intake.gender or None,
        height_cm=intake.height_cm,
        weight_kg=intake.weight_kg,
        primary_sport=resolve_primary_sport(plan_track, intake),
        sport_position=(intake.sport_position or None) if plan_track == "sport" else None,
        season_phase=normalize_season_phase(intake.season_phase) if plan_track == "sport" else None,
        weekly_competitions=intake.weekly_competitions if plan_track == "sport" else None,
        experience_level=intake.experience_level or None,
        training_days_per_week=intake.training_days_per_week,
        session_duration_minutes=intake.session_duration_minutes,
        equipment_access=intake.equipment_access,
        performance_priorities=intake.performance_priorities if plan_track == "sport" else [],
        limitations_notes=intake.limitations_notes or None,
        goal_title=intake.goal_title or intake.request_text or "Performance development",
        goal_type=intake.goal_type,
        duration_weeks=intake.duration_weeks,
        start_date=intake.start_date,
        timezone=intake.timezone or "UTC",
    )


def build_generation_request(
    plan_track: str,
    intake: ConversationIntakeState,
    preview: WorkoutPlanPreviewResponse,
) -> WorkoutGenerationRequest:
    return WorkoutGenerationRequest(
        goal_id=None,
        focus=None,
        title=None,
        description=None,
        start_date=intake.start_date,
        sessions_per_week=intake.training_days_per_week,
        duration_weeks=preview.preview_plan.duration_weeks,
        sport_position=(intake.sport_position or None) if plan_track == "sport" else None,
        season_phase=normalize_season_phase(intake.season_phase) if plan_track == "sport" else None,
        weekly_competitions=intake.weekly_competitions if plan_track == "sport" else None,
        performance_priorities=intake.performance_priorities if plan_track == "sport" else [],
        equipment_access=intake.equipment_access,
        limitations_notes=intake.limitations_notes or None,
        save_plan=True,
    )


def build_local_email(full_name: str, conversation_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", ".", normalize_text(full_name)).strip(".") or "hybrid-athlete"
    return f"{slug}.{conversation_id[:8]}@local.hybrid-athlete"


conversation_service = ConversationService()
