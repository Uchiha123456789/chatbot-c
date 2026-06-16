"""Hash mật khẩu (bcrypt) và lấy user hiện tại từ session cookie."""
import bcrypt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

USERNAME_MIN_LENGTH = 3
PASSWORD_MIN_LENGTH = 6


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency bắt buộc đăng nhập — ném 401 nếu chưa có session hợp lệ."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập")

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập không hợp lệ")

    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Dependency cho trang có thể xem mà không cần đăng nhập (vd trang chủ điều hướng)."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)
