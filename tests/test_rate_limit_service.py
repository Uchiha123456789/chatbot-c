"""Test cho rate_limit_service — fixed-window counter giới hạn /api/ask theo user_id."""
import pytest
from fastapi import HTTPException

from services import rate_limit_service as rl


@pytest.fixture(autouse=True)
def _clean_counters():
    rl.reset_rate_limit()
    yield
    rl.reset_rate_limit()


def test_allows_requests_up_to_the_limit():
    for _ in range(5):
        rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)
    # không raise -> hợp lệ


def test_blocks_request_beyond_limit_with_429():
    for _ in range(5):
        rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)

    with pytest.raises(HTTPException) as exc_info:
        rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


def test_counters_are_independent_per_user():
    for _ in range(5):
        rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)

    # user khác chưa vượt giới hạn -> không raise
    rl.check_rate_limit(user_id=2, max_requests=5, window_seconds=60)


def test_counter_resets_in_a_new_window(monkeypatch):
    fake_now = [1_000_000]
    monkeypatch.setattr(rl.time, "time", lambda: fake_now[0])

    for _ in range(5):
        rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)
    with pytest.raises(HTTPException):
        rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)

    # nhảy sang cửa sổ kế tiếp -> bộ đếm reset, request lại được chấp nhận
    fake_now[0] += 60
    rl.check_rate_limit(user_id=1, max_requests=5, window_seconds=60)
