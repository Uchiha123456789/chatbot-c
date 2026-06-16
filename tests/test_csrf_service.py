"""Test cho csrf_service — lớp giảm thiểu CSRF dựa trên header tuỳ chỉnh."""
import pytest

from services.csrf_service import has_valid_csrf_header, requires_csrf_header


@pytest.mark.parametrize(
    "method, path, expected",
    [
        ("POST", "/api/ask", True),
        ("PUT", "/api/messages/1/feedback", True),
        ("PATCH", "/api/conversations/1", True),
        ("DELETE", "/api/conversations/1", True),
        ("POST", "/auth/login", True),
        ("POST", "/auth/register", True),
        ("GET", "/api/conversations", False),  # an toàn — không thay đổi trạng thái
        ("HEAD", "/api/conversations", False),
        ("OPTIONS", "/api/conversations", False),
        ("POST", "/chat", False),  # ngoài phạm vi /api, /auth (page điều hướng thường)
        ("POST", "/static/js/chat.js", False),
    ],
)
def test_requires_csrf_header(method, path, expected):
    assert requires_csrf_header(method, path) is expected


def test_has_valid_csrf_header_accepts_expected_value():
    assert has_valid_csrf_header({"x-requested-with": "fetch"}) is True


def test_has_valid_csrf_header_is_case_insensitive_on_value():
    assert has_valid_csrf_header({"x-requested-with": "Fetch"}) is True


def test_has_valid_csrf_header_rejects_missing_header():
    assert has_valid_csrf_header({}) is False


def test_has_valid_csrf_header_rejects_wrong_value():
    assert has_valid_csrf_header({"x-requested-with": "XMLHttpRequest"}) is False
