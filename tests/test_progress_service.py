"""Test cho progress_service — thuật toán SM-2 rút gọn theo dõi tiến độ học.

Chỉ kiểm tra các hàm thuần (`_quality_from_score`, `apply_sm2_update`) trên
một đối tượng TopicProgress dựng tay — không cần DB/HTTP, để có thể chạy
nhanh và độc lập trong `pytest tests/`.
"""
from datetime import datetime, timedelta

import pytest

from models.topic_progress import TopicProgress
from services.progress_service import EMA_WEIGHT, _quality_from_score, apply_sm2_update


def _new_progress() -> TopicProgress:
    return TopicProgress(
        user_id=1,
        topic_id=1,
        mastery_level=0.0,
        ease_factor=2.5,
        interval_days=1,
        repetitions=0,
    )


@pytest.mark.parametrize(
    "score, expected_quality",
    [(1.0, 5), (0.9, 5), (0.8, 4), (0.7, 4), (0.6, 3), (0.5, 3), (0.4, 2), (0.3, 2), (0.2, 1), (0.1, 1), (0.0, 0)],
)
def test_quality_from_score_thresholds(score, expected_quality):
    assert _quality_from_score(score) == expected_quality


def test_first_good_review_sets_interval_one_and_increments_repetitions():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)

    apply_sm2_update(progress, score=0.95, now=now)

    assert progress.repetitions == 1
    assert progress.interval_days == 1
    assert progress.last_reviewed_at == now
    assert progress.next_review_at == now + timedelta(days=1)
    assert progress.mastery_level == pytest.approx((1 - EMA_WEIGHT) * 0.0 + EMA_WEIGHT * 0.95)
    assert progress.ease_factor > 2.5  # q=5 -> ease tăng


def test_second_good_review_sets_interval_six():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)
    apply_sm2_update(progress, score=0.95, now=now)
    apply_sm2_update(progress, score=0.95, now=now + timedelta(days=1))

    assert progress.repetitions == 2
    assert progress.interval_days == 6


def test_third_good_review_multiplies_interval_by_ease_factor():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)
    apply_sm2_update(progress, score=0.95, now=now)
    apply_sm2_update(progress, score=0.95, now=now)
    ease_before_third = progress.ease_factor
    interval_before_third = progress.interval_days

    apply_sm2_update(progress, score=0.95, now=now)

    assert progress.repetitions == 3
    assert progress.interval_days == max(1, round(interval_before_third * ease_before_third))


def test_low_quality_review_resets_repetitions_and_interval():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)
    apply_sm2_update(progress, score=0.95, now=now)
    apply_sm2_update(progress, score=0.95, now=now)
    assert progress.repetitions == 2

    apply_sm2_update(progress, score=0.1, now=now)

    assert progress.repetitions == 0
    assert progress.interval_days == 1


def test_ease_factor_never_drops_below_floor():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)

    for _ in range(20):
        apply_sm2_update(progress, score=0.0, now=now)

    assert progress.ease_factor >= 1.3
    assert progress.ease_factor == pytest.approx(1.3)


def test_mastery_level_is_exponential_moving_average():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)

    apply_sm2_update(progress, score=0.8, now=now)
    expected_first = (1 - EMA_WEIGHT) * 0.0 + EMA_WEIGHT * 0.8
    assert progress.mastery_level == pytest.approx(expected_first)

    apply_sm2_update(progress, score=0.4, now=now)
    expected_second = (1 - EMA_WEIGHT) * expected_first + EMA_WEIGHT * 0.4
    assert progress.mastery_level == pytest.approx(expected_second)


def test_score_outside_unit_range_is_clamped():
    progress = _new_progress()
    now = datetime(2026, 1, 1, 12, 0, 0)

    apply_sm2_update(progress, score=5.0, now=now)
    assert progress.mastery_level == pytest.approx(EMA_WEIGHT * 1.0)
