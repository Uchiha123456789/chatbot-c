# Cơ sở dữ liệu

CSDL quan hệ: **SQLite** tại `data/app.db`, truy cập qua **SQLAlchemy ORM** (model trong `models/`). Lý do chọn ORM thay vì `sqlite3` thô: parameterized query có sẵn (chống SQL injection — xem [security.md](security.md)), model ORM đồng thời là tài liệu schema cho báo cáo.

## Nguyên tắc song song với Chroma (polyglot persistence)

- **SQLite**: dữ liệu có cấu trúc, quan hệ, giao dịch — user, hội thoại, tin nhắn, quiz, feedback, tiến độ học.
- **Chroma** (`chroma_db/`, collection `giao_trinh_c`): dữ liệu ngữ nghĩa không cấu trúc — chunk giáo trình + embedding, phục vụ semantic search cho RAG.
- Cầu nối giữa hai bên: cột `messages.retrieved_chunk_ids` (JSON array các id chunk trong Chroma đã dùng làm context) — cho phép truy vết (provenance) câu trả lời nào dựa trên đoạn tài liệu nào.

## Schema (DDL sketch)

```sql
-- USERS
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    email           TEXT UNIQUE,
    password_hash   TEXT NOT NULL,            -- bcrypt hash, không lưu plaintext
    display_name    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at   TEXT
);
CREATE INDEX idx_users_username ON users(username);

-- CONVERSATIONS ("project" hội thoại)
CREATE TABLE conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    is_archived     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_conversations_user_updated ON conversations(user_id, updated_at DESC);

-- MESSAGES
CREATE TABLE messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
    content         TEXT NOT NULL,
    retrieved_chunk_ids TEXT,           -- JSON array id chunk Chroma dùng làm context
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_messages_conv_created ON messages(conversation_id, created_at);

-- FEEDBACK (like/dislike từng tin nhắn assistant)
CREATE TABLE feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating          INTEGER NOT NULL CHECK (rating IN (-1, 1)),
    comment         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(message_id, user_id)
);

-- TOPICS (taxonomy chủ đề — seed từ field "topic" trong test_questions.json)
CREATE TABLE topics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,        -- "biến", "vòng lặp", "con trỏ", ...
    description     TEXT
);

-- QUIZZES / QUESTIONS
CREATE TABLE quizzes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id        INTEGER REFERENCES topics(id),
    title           TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_type   TEXT NOT NULL CHECK (question_type IN ('mcq','code','short_answer')),
    prompt          TEXT NOT NULL,
    reference_answer TEXT,
    grading_rubric  TEXT,                  -- JSON: keyword/test case/trọng số từng tiêu chí
    difficulty      INTEGER NOT NULL DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5)
);

-- ATTEMPTS / SUBMISSIONS
CREATE TABLE quiz_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT,
    total_score     REAL
);
CREATE TABLE submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id      INTEGER NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    student_answer  TEXT NOT NULL,
    score           REAL NOT NULL DEFAULT 0,
    grading_detail  TEXT,                  -- JSON: chi tiết chấm theo từng tiêu chí
    graded_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_submissions_attempt ON submissions(attempt_id);

-- TOPIC PROGRESS (trạng thái SM-2 đơn giản hoá — xem algorithms.md)
CREATE TABLE topic_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id        INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    mastery_level   REAL NOT NULL DEFAULT 0,
    ease_factor     REAL NOT NULL DEFAULT 2.5,
    interval_days   INTEGER NOT NULL DEFAULT 1,
    repetitions     INTEGER NOT NULL DEFAULT 0,
    last_reviewed_at TEXT,
    next_review_at  TEXT,
    UNIQUE(user_id, topic_id)
);
CREATE INDEX idx_progress_user_next ON topic_progress(user_id, next_review_at);
```

## Quy ước

- Tên bảng: số nhiều, snake_case (`conversations`, `quiz_attempts`)
- Khoá ngoại luôn `<table_singular>_id`, có index khi dùng để lọc/join thường xuyên
- Timestamp lưu dạng `TEXT` ISO (`datetime('now')`) — SQLite không có kiểu DATETIME thật
- Trường JSON (`retrieved_chunk_ids`, `grading_rubric`, `grading_detail`) lưu dạng `TEXT`, parse/serialize ở tầng service — giữ schema đơn giản, tránh JSON1 extension nếu không cần
- `ON DELETE CASCADE` cho mọi quan hệ con phụ thuộc vòng đời cha (xoá user → xoá hội thoại/feedback/progress liên quan)
- Bật `PRAGMA journal_mode=WAL` khi khởi tạo engine — xem [ops.md](ops.md)
