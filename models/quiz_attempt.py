from datetime import datetime

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_attempts_user_quiz", "user_id", "quiz_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    total_score: Mapped[float | None] = mapped_column(nullable=True)

    quiz: Mapped["Quiz"] = relationship()
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan", order_by="Submission.id"
    )
