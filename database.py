import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    # 🌟 CẬP NHẬT: Thêm timeout để tránh lỗi "database is locked" khi nhiều người ghi cùng lúc
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Đợi tối đa 30 giây nếu DB đang bận trước khi báo lỗi
    },
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")       # 
    cursor.execute("PRAGMA synchronous=NORMAL")   # 
    # 🌟 BỔ SUNG: Bật tính năng cache bộ nhớ để SQLite truy vấn nhanh hơn
    cursor.execute("PRAGMA cache_size=-2000")     # Sử dụng khoảng 2MB bộ nhớ đệm cho cache
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# 
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db(): # 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()