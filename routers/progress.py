from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.topic import Topic
from models.topic_progress import TopicProgress
from models.user import User
from schemas.progress import ProgressDashboardOut, TopicProgressOut
from services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress", response_model=ProgressDashboardOut)
def get_progress(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(TopicProgress, Topic)
        .join(Topic, TopicProgress.topic_id == Topic.id)
        .filter(TopicProgress.user_id == user.id)
        .order_by(Topic.name)
        .all()
    )

    now = datetime.utcnow()
    topics: list[TopicProgressOut] = []
    for progress, topic in rows:
        is_due = progress.next_review_at is not None and progress.next_review_at <= now
        topics.append(
            TopicProgressOut(
                topic_id=topic.id,
                topic_name=topic.name,
                mastery_level=progress.mastery_level,
                ease_factor=progress.ease_factor,
                interval_days=progress.interval_days,
                repetitions=progress.repetitions,
                last_reviewed_at=progress.last_reviewed_at,
                next_review_at=progress.next_review_at,
                is_due=is_due,
            )
        )

    due_today = [t for t in topics if t.is_due]
    due_today.sort(key=lambda t: t.next_review_at or datetime.min)

    return ProgressDashboardOut(topics=topics, due_today=due_today)
