import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User
from schemas.chat import (
    AskRequest,
    AskResponse,
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageOut,
)
from services.auth_service import get_current_user
from services.rag_service import get_rag_service
from services.rate_limit_service import check_rate_limit

router = APIRouter(prefix="/api", tags=["chat"])

DEFAULT_PAGE_SIZE = 20
MAX_HISTORY_MESSAGES = 20


def _get_owned_conversation(conversation_id: int, user: User, db: Session) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hội thoại")
    return conversation


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    before: datetime | None = Query(default=None, description="Cursor: chỉ lấy hội thoại cập nhật trước thời điểm này"),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Conversation).filter(
        Conversation.user_id == user.id,
        Conversation.is_archived.is_(False),
    )
    if before is not None:
        query = query.filter(Conversation.updated_at < before)

    return query.order_by(Conversation.updated_at.desc()).limit(limit).all()


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = Conversation(user_id=user.id, title=payload.title or "Cuộc trò chuyện mới")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = _get_owned_conversation(conversation_id, user, db)
    if payload.title is not None:
        conversation.title = payload.title
    if payload.is_archived is not None:
        conversation.is_archived = payload.is_archived
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = _get_owned_conversation(conversation_id, user, db)
    db.delete(conversation)
    db.commit()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: int,
    before_id: int | None = Query(default=None, description="Cursor: chỉ lấy tin nhắn có id nhỏ hơn giá trị này"),
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = _get_owned_conversation(conversation_id, user, db)

    query = db.query(Message).filter(Message.conversation_id == conversation.id)
    if before_id is not None:
        query = query.filter(Message.id < before_id)

    messages = query.order_by(Message.id.desc()).limit(limit).all()
    messages.reverse()
    return messages


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(user.id)
    conversation = _get_owned_conversation(payload.conversation_id, user, db)

    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(recent_messages)]

    rag = get_rag_service()
    answer, chunk_ids = rag.ask(payload.question, history)

    user_message = Message(conversation_id=conversation.id, role="user", content=payload.question)
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        retrieved_chunk_ids=json.dumps(chunk_ids, ensure_ascii=False),
    )
    db.add_all([user_message, assistant_message])

    conversation.updated_at = datetime.utcnow()
    if conversation.title == "Cuộc trò chuyện mới":
        conversation.title = payload.question.strip()[:60]

    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return AskResponse(
        answer=answer,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        retrieved_chunk_ids=chunk_ids,
    )
