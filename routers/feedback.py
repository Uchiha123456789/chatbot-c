from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.feedback import Feedback
from models.message import Message
from models.user import User
from schemas.feedback import FeedbackOut, FeedbackUpsert
from services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["feedback"])


def _get_owned_message(message_id: int, user: User, db: Session) -> Message:
    message = db.get(Message, message_id)
    if message is None or message.role != "assistant" or message.conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tin nhắn")
    return message


@router.put("/messages/{message_id}/feedback", response_model=FeedbackOut)
def upsert_feedback(
    message_id: int,
    payload: FeedbackUpsert,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = _get_owned_message(message_id, user, db)

    feedback = (
        db.query(Feedback)
        .filter(Feedback.message_id == message.id, Feedback.user_id == user.id)
        .one_or_none()
    )
    if feedback is None:
        feedback = Feedback(message_id=message.id, user_id=user.id, rating=payload.rating, comment=payload.comment)
        db.add(feedback)
    else:
        feedback.rating = payload.rating
        feedback.comment = payload.comment

    db.commit()
    db.refresh(feedback)
    return feedback


@router.delete("/messages/{message_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    message_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = _get_owned_message(message_id, user, db)

    feedback = (
        db.query(Feedback)
        .filter(Feedback.message_id == message.id, Feedback.user_id == user.id)
        .one_or_none()
    )
    if feedback is not None:
        db.delete(feedback)
        db.commit()
