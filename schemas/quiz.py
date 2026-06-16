from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TopicOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class QuizOut(BaseModel):
    id: int
    topic_id: int | None = None
    title: str
    created_at: datetime
    question_count: int = 0

    model_config = {"from_attributes": True}


class QuestionForStudent(BaseModel):
    """Câu hỏi gửi cho học viên — KHÔNG kèm reference_answer/grading_rubric để tránh lộ đáp án."""

    id: int
    question_type: Literal["mcq", "code", "short_answer"]
    prompt: str
    difficulty: int

    model_config = {"from_attributes": True}


class QuizDetailOut(BaseModel):
    id: int
    topic_id: int | None = None
    title: str
    created_at: datetime
    questions: list[QuestionForStudent]

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: int
    student_answer: str = Field(min_length=1, max_length=4000)


class AttemptSubmitRequest(BaseModel):
    answers: list[AnswerSubmit] = Field(min_length=1, max_length=50)


class SubmissionOut(BaseModel):
    question_id: int
    question_type: str
    prompt: str
    student_answer: str
    score: float
    grading_detail: dict[str, Any]

    model_config = {"from_attributes": True}


class AttemptResultOut(BaseModel):
    id: int
    quiz_id: int
    started_at: datetime
    completed_at: datetime | None
    total_score: float | None
    submissions: list[SubmissionOut]

    model_config = {"from_attributes": True}
