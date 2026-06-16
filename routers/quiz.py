import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.question import Question
from models.quiz import Quiz
from models.quiz_attempt import QuizAttempt
from models.submission import Submission
from models.topic import Topic
from models.user import User
from schemas.quiz import (
    AttemptResultOut,
    AttemptSubmitRequest,
    QuizDetailOut,
    QuizOut,
    SubmissionOut,
    TopicOut,
)
from services.auth_service import get_current_user
from services.grading_service import grade_answer
from services.progress_service import record_quiz_result
from services.rag_service import get_rag_service

router = APIRouter(prefix="/api", tags=["quiz"])


@router.get("/topics", response_model=list[TopicOut])
def list_topics(db: Session = Depends(get_db)):
    return db.query(Topic).order_by(Topic.name).all()


@router.get("/quizzes", response_model=list[QuizOut])
def list_quizzes(
    topic_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Quiz)
    if topic_id is not None:
        query = query.filter(Quiz.topic_id == topic_id)

    quizzes = query.order_by(Quiz.created_at.desc()).all()
    return [
        QuizOut(
            id=quiz.id,
            topic_id=quiz.topic_id,
            title=quiz.title,
            created_at=quiz.created_at,
            question_count=len(quiz.questions),
        )
        for quiz in quizzes
    ]


@router.get("/quizzes/{quiz_id}", response_model=QuizDetailOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài quiz")
    return quiz


@router.post("/quizzes/{quiz_id}/attempt", response_model=AttemptResultOut, status_code=status.HTTP_201_CREATED)
def submit_attempt(
    quiz_id: int,
    payload: AttemptSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài quiz")

    questions_by_id = {q.id: q for q in quiz.questions}
    answers_by_question = {a.question_id: a for a in payload.answers}

    unknown_ids = set(answers_by_question) - set(questions_by_id)
    if unknown_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Câu hỏi không thuộc bài quiz này: {sorted(unknown_ids)}",
        )

    rag = get_rag_service()
    attempt = QuizAttempt(user_id=user.id, quiz_id=quiz.id)
    db.add(attempt)
    db.flush()

    submissions: list[Submission] = []
    scores: list[float] = []
    for question in questions_by_id.values():
        answer = answers_by_question.get(question.id)
        student_answer = answer.student_answer if answer else ""

        score, detail = grade_answer(
            question_type=question.question_type,
            student_answer=student_answer,
            reference_answer=question.reference_answer,
            grading_rubric_json=question.grading_rubric,
            embed_fn=rag.embed_text,
        )
        scores.append(score)
        submissions.append(
            Submission(
                attempt_id=attempt.id,
                question_id=question.id,
                student_answer=student_answer,
                score=score,
                grading_detail=_dump_detail(detail),
            )
        )

    db.add_all(submissions)
    attempt.completed_at = datetime.utcnow()
    attempt.total_score = sum(scores) / len(scores) if scores else 0.0

    if quiz.topic_id is not None and scores:
        record_quiz_result(db, user_id=user.id, topic_id=quiz.topic_id, score=attempt.total_score, now=attempt.completed_at)

    db.commit()
    db.refresh(attempt)

    return AttemptResultOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        total_score=attempt.total_score,
        submissions=[
            SubmissionOut(
                question_id=submission.question_id,
                question_type=questions_by_id[submission.question_id].question_type,
                prompt=questions_by_id[submission.question_id].prompt,
                student_answer=submission.student_answer,
                score=submission.score,
                grading_detail=_load_detail(submission.grading_detail),
            )
            for submission in submissions
        ],
    )


def _dump_detail(detail: dict) -> str:
    return json.dumps(detail, ensure_ascii=False)


def _load_detail(detail_json: str | None) -> dict:
    if not detail_json:
        return {}
    try:
        return json.loads(detail_json)
    except (TypeError, ValueError):
        return {}
