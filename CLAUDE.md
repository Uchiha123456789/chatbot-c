# CLAUDE.md — Chatbot học lập trình C

Hướng dẫn cho Claude Code (và bất kỳ ai) khi làm việc trên dự án này.

## Dự án là gì

Chatbot RAG hỗ trợ sinh viên/học sinh học lập trình C, trả lời bằng tiếng Việt, dựa trên giáo trình "Kỹ thuật lập trình C" đã được nhúng vào vector store. Đây là đồ án tốt nghiệp — code cần vừa chạy thật vừa thể hiện được chiều sâu thiết kế (CSDL, giải thuật, bảo mật, khả năng mở rộng, sao lưu/khôi phục) để viết báo cáo.

Kế hoạch tổng thể (đang thực hiện) nằm ở: `C:\Users\honghuee\.claude\plans\m-nh-mu-n-x-y-d-ng-scalable-lemon.md`.

## Stack

- **Backend**: FastAPI + Uvicorn, Jinja2 cho page shell, REST JSON API cho phần động
- **CSDL quan hệ**: SQLite qua SQLAlchemy ORM (`data/app.db`)
- **Vector store**: ChromaDB persistent (`chroma_db/`, collection `giao_trinh_c`) — giữ nguyên cho RAG
- **LLM**: Groq (`llama-3.3-70b-versatile`) qua Groq SDK
- **Embedding**: Google Gemini (`models/text-embedding-004`) qua `langchain-google-genai` (cloud, free tier)
- **Auth**: session cookie ký bằng `itsdangerous` (Starlette `SessionMiddleware`)
- **Frontend**: HTML/CSS/JS thuần (không React/build step), `fetch()` gọi API

> Đã loại bỏ Streamlit (`app.py` cũ) — `main.py` (FastAPI) là entry point hiện tại. Logic RAG đã chuyển vào `services/rag_service.py` (dùng chung cho web, CLI `chatbot.py`, và benchmark `test.py`).

## Cấu trúc thư mục (mục tiêu)

```
chatbot-c/
  main.py, config.py, database.py
  models/      # SQLAlchemy ORM
  schemas/     # Pydantic request/response
  routers/     # FastAPI routers theo domain
  services/    # rag_service, chunking, auth_service, grading_service, progress_service
  templates/   # Jinja2 page shell
  static/      # css/, js/
  ingest.py
  scripts/     # backup_db.py, restore_db.py
  data/app.db, data/source/, backups/, chroma_db/
  tests/
  Dockerfile, docker-compose.yml, .dockerignore, Caddyfile
```

## Quy ước code

- UI và prompt gửi LLM: **tiếng Việt**, thân thiện, luôn kèm ví dụ code khi giải thích khái niệm C
- Tên biến/hàm/bảng/route: **tiếng Anh**, snake_case cho Python & SQL, camelCase cho JS
- Mọi truy vấn DB qua SQLAlchemy ORM (không string-format SQL)
- Mọi request body validate qua Pydantic schema
- Không commit `.env`, `data/app.db`, `chroma_db/`, `venv/`, `backups/`

## Lệnh thường dùng

```
uvicorn main:app --reload          # chạy dev server FastAPI (http://127.0.0.1:8000)
python chatbot.py                  # CLI smoke-test cho RagService
python ingest.py                   # nhúng lại giáo trình PDF vào Chroma
python test.py                     # benchmark bộ câu hỏi mẫu, lưu test_result_*.json
python scripts/seed_quizzes.py     # seed topics/quizzes/questions mẫu (giai đoạn 3, idempotent)
pytest tests/                      # chạy test cho services thuần
python scripts/backup_db.py        # sao lưu SQLite + Chroma (giai đoạn 5)
python scripts/restore_db.py <file>  # khôi phục từ bản sao lưu (giai đoạn 5)
```

## Tài liệu chi tiết theo mảng

| Mảng | File | Nội dung |
|---|---|---|
| Cơ sở dữ liệu | [docs/claude/database.md](docs/claude/database.md) | Schema SQLite, FK/index, quy ước đặt tên, quan hệ với Chroma |
| Giải thuật | [docs/claude/algorithms.md](docs/claude/algorithms.md) | Pipeline RAG, chấm điểm code, SM-2 tiến độ học, phân trang |
| Bảo mật | [docs/claude/security.md](docs/claude/security.md) | Quy tắc bắt buộc: hash mật khẩu, chống injection/CSRF/XSS, prompt-injection, rate limit |
| Giao diện | [docs/claude/ui.md](docs/claude/ui.md) | Layout từng trang, style guide, cách gọi API, render Markdown an toàn |
| Vận hành | [docs/claude/ops.md](docs/claude/ops.md) | Biến môi trường, backup/restore, khả năng mở rộng |

Khi thêm code mới ở mảng nào, đọc file con tương ứng trước để tuân đúng quy ước đã thống nhất.
