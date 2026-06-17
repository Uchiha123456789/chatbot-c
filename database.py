import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

_database_url = settings.database_url

if _database_url:
    # PostgreSQL (hoặc bất kỳ DB nào được truyền qua DATABASE_URL)
    # psycopg2 yêu cầu scheme "postgresql+psycopg2://" — tự động fix nếu Render/Heroku trả về "postgres://"
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    engine = create_engine(_database_url, pool_pre_ping=True)
    _is_sqlite = False
else:
    # Fallback SQLite cho local dev
    os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)
    engine = create_engine(
        f"sqlite:///{settings.db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    _is_sqlite = True


if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-2000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()