from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("question_type IN ('mcq','code','short_answer')", name="ck_questions_type"),
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_questions_difficulty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    question_type: Mapped[str] = mapped_column(String(16))
    prompt: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    grading_rubric: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
