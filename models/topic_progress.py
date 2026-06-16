from datetime import datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TopicProgress(Base):
    """Trạng thái ôn tập theo cặp (user, topic) — cập nhật bởi progress_service (SM-2)."""

    __tablename__ = "topic_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_progress_user_topic"),
        Index("idx_progress_user_next", "user_id", "next_review_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    mastery_level: Mapped[float] = mapped_column(default=0.0)
    ease_factor: Mapped[float] = mapped_column(default=2.5)
    interval_days: Mapped[int] = mapped_column(default=1)
    repetitions: Mapped[int] = mapped_column(default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(nullable=True)

    topic: Mapped["Topic"] = relationship()
