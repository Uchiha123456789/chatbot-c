from datetime import datetime

from pydantic import BaseModel


class TopicProgressOut(BaseModel):
    topic_id: int
    topic_name: str
    mastery_level: float
    ease_factor: float
    interval_days: int
    repetitions: int
    last_reviewed_at: datetime | None
    next_review_at: datetime | None
    is_due: bool

    model_config = {"from_attributes": True}


class ProgressDashboardOut(BaseModel):
    topics: list[TopicProgressOut]
    due_today: list[TopicProgressOut]
