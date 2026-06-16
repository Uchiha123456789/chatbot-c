"""progress_service: cập nhật trạng thái ôn tập (user, topic) theo thuật toán SM-2 rút gọn.

Xem docs/claude/algorithms.md mục 3 — mỗi (user_id, topic_id) là một state machine
độc lập, được cập nhật mỗi khi người dùng hoàn thành một lượt làm quiz thuộc chủ đề đó.

Bước 1 — suy ra "chất lượng nhớ lại" q ∈ [0..5] từ điểm bài làm (score ∈ [0,1]):
    score >= 0.9 → q=5 ; >= 0.7 → q=4 ; >= 0.5 → q=3
    >= 0.3 → q=2 ; >= 0.1 → q=1 ; else → q=0

Bước 2 — cập nhật repetitions/interval_days theo SM-2 (Wozniak):
    q >= 3: lặp lại đúng hạn → tăng repetitions, nới rộng interval
    q <  3: quên → reset repetitions về 0, ôn lại sau 1 ngày

Bước 3 — cập nhật ease_factor (độ "dễ nhớ" — hệ số nhân interval lần sau),
luôn giữ >= 1.3 để tránh interval co lại quá nhanh.

Bước 4 — mastery_level cập nhật theo trung bình động hàm mũ (EMA), trọng số 0.3
cho lần làm mới nhất — phản ánh xu hướng gần đây nhưng không quá nhạy với 1 lần làm.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.topic_progress import TopicProgress

EMA_WEIGHT = 0.3


def _quality_from_score(score: float) -> int:
    if score >= 0.9:
        return 5
    if score >= 0.7:
        return 4
    if score >= 0.5:
        return 3
    if score >= 0.3:
        return 2
    if score >= 0.1:
        return 1
    return 0


def apply_sm2_update(progress: TopicProgress, score: float, *, now: datetime | None = None) -> TopicProgress:
    """Cập nhật một bản ghi TopicProgress tại chỗ theo công thức SM-2 rút gọn, trả về chính nó."""
    now = now or datetime.utcnow()
    score = max(0.0, min(1.0, score))
    quality = _quality_from_score(score)

    if quality >= 3:
        if progress.repetitions == 0:
            interval = 1
        elif progress.repetitions == 1:
            interval = 6
        else:
            interval = max(1, round(progress.interval_days * progress.ease_factor))
        progress.repetitions += 1
    else:
        progress.repetitions = 0
        interval = 1

    progress.ease_factor = max(
        1.3,
        progress.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    progress.interval_days = interval
    progress.last_reviewed_at = now
    progress.next_review_at = now + timedelta(days=interval)
    progress.mastery_level = (1 - EMA_WEIGHT) * progress.mastery_level + EMA_WEIGHT * score

    return progress


def record_quiz_result(db: Session, user_id: int, topic_id: int, score: float, *, now: datetime | None = None) -> TopicProgress:
    """Lấy (hoặc tạo mới) TopicProgress của (user, topic) rồi áp dụng cập nhật SM-2.

    Không commit — để router gộp chung vào transaction lưu attempt/submissions.
    """
    progress = (
        db.query(TopicProgress)
        .filter(TopicProgress.user_id == user_id, TopicProgress.topic_id == topic_id)
        .one_or_none()
    )
    if progress is None:
        progress = TopicProgress(
            user_id=user_id,
            topic_id=topic_id,
            mastery_level=0.0,
            ease_factor=2.5,
            interval_days=1,
            repetitions=0,
        )
        db.add(progress)

    apply_sm2_update(progress, score, now=now)
    return progress
