from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("idx_submissions_attempt", "attempt_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    student_answer: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(default=0)
    grading_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    graded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    attempt: Mapped["QuizAttempt"] = relationship(back_populates="submissions")
    question: Mapped["Question"] = relationship()
