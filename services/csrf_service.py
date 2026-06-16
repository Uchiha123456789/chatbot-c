"""csrf_service: lớp giảm thiểu CSRF nhẹ cho API JSON (`fetch`).

Theo docs/claude/security.md: API JSON dựa vào same-site session cookie +
kiểm tra header tuỳ chỉnh `X-Requested-With`. Trình duyệt KHÔNG cho phép một
trang web khác (cross-site form submit / <img>/<script> request) tự thêm
header tuỳ chỉnh vào request mà không kích hoạt CORS preflight — nên việc bắt
buộc header này có mặt trên các request làm thay đổi trạng thái (POST/PUT/
PATCH/DELETE) tới `/api/*` và `/auth/*` chặn được CSRF cổ điển dựa trên cookie.

`apiFetch` (static/js/common.js) đã luôn gửi kèm header này — middleware ở đây
chỉ là phần xác thực phía server còn thiếu để quy tắc thực sự có hiệu lực.
"""
CSRF_HEADER_NAME = "x-requested-with"
CSRF_HEADER_VALUE = "fetch"

PROTECTED_PREFIXES = ("/api/", "/auth/")
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def requires_csrf_header(method: str, path: str) -> bool:
    """True nếu request này phải kèm header X-Requested-With hợp lệ."""
    if method.upper() in SAFE_METHODS:
        return False
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def has_valid_csrf_header(headers) -> bool:
    """`headers` là mapping case-insensitive (vd starlette Headers/dict)."""
    return headers.get(CSRF_HEADER_NAME, "").lower() == CSRF_HEADER_VALUE
