"""rate_limit_service: giới hạn số request/phút trên /api/ask theo user_id.

Thuật toán: fixed-window counter — đếm số request trong "cửa sổ" thời gian hiện
tại (mốc làm tròn xuống bội số của WINDOW_SECONDS); khi request rơi vào cửa sổ
mới, bộ đếm reset về 0. Đơn giản, đủ dùng cho quy mô đồ án (vài chục-vài trăm
người dùng đồng thời) và không cần hạ tầng ngoài (Redis...) — lưu trong bộ nhớ
tiến trình, bảo vệ bằng khoá để an toàn khi nhiều thread cùng truy cập
(FastAPI chạy endpoint đồng bộ trong threadpool).

Mục đích: bảo vệ quota Groq API và tránh một người dùng chiếm hết tài nguyên.
"""
import threading
import time

from fastapi import HTTPException, status

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 10

_lock = threading.Lock()
_counters: dict[int, tuple[int, int]] = {}  # user_id -> (mốc cửa sổ, số request đã đếm)


def check_rate_limit(
    user_id: int,
    *,
    max_requests: int = MAX_REQUESTS_PER_WINDOW,
    window_seconds: int = WINDOW_SECONDS,
) -> None:
    """Tăng bộ đếm cho user_id; ném HTTP 429 nếu vượt giới hạn trong cửa sổ hiện tại."""
    now = int(time.time())
    window_start = now - (now % window_seconds)

    with _lock:
        recorded_window, count = _counters.get(user_id, (window_start, 0))
        if recorded_window != window_start:
            recorded_window, count = window_start, 0
        count += 1
        _counters[user_id] = (recorded_window, count)

    if count > max_requests:
        retry_after = window_seconds - (now - recorded_window)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Bạn đã hỏi quá nhiều trong thời gian ngắn — vui lòng thử lại sau {retry_after} giây.",
            headers={"Retry-After": str(retry_after)},
        )


def reset_rate_limit() -> None:
    """Xoá toàn bộ bộ đếm — chỉ dùng cho test tự động để cô lập từng test case."""
    with _lock:
        _counters.clear()
