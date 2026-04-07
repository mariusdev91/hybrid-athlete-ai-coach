from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db_rel.session import get_db
from app.schemas.ai import ConversationConfirmResponse
from app.schemas.ai import ConversationCreateRequest
from app.schemas.ai import ConversationMessageCreate
from app.schemas.ai import ConversationRead
from app.services.conversation_service import conversation_service


router = APIRouter()


@router.post("/conversations", response_model=ConversationRead, status_code=201)
def create_conversation(
    payload: ConversationCreateRequest,
    db: Session = Depends(get_db),
):
    return conversation_service.create_conversation(db, payload)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    return conversation_service.get_conversation(db, conversation_id)


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationRead)
def send_conversation_message(
    conversation_id: str,
    payload: ConversationMessageCreate,
    db: Session = Depends(get_db),
):
    return conversation_service.submit_message(db, conversation_id, payload)


@router.post("/conversations/{conversation_id}/confirm", response_model=ConversationConfirmResponse)
def confirm_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    return conversation_service.confirm_conversation(db, conversation_id)
