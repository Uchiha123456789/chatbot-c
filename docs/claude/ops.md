# Vận hành (Ops)

## Biến môi trường (`.env`)

| Biến | Mục đích |
|---|---|
| `GROQ_API_KEY` | Gọi Groq LLM API (sinh câu trả lời) |
| `GOOGLE_API_KEY` | Gọi Google Gemini API cho embedding (`langchain-google-genai`) — **bắt buộc** |
| `SECRET_KEY` | Ký session cookie (`itsdangerous`/`SessionMiddleware`) |
| (tuỳ chọn) `EMBEDDING_MODEL` | Đổi model embedding (mặc định `models/gemini-embedding-001`) |
| (tuỳ chọn) `SESSION_HTTPS_ONLY` | `true` trên VPS có HTTPS — cookie session chỉ gửi qua HTTPS |
| (tuỳ chọn) `DB_PATH`, `CHROMA_DIR` | Đường dẫn DB/Chroma nếu muốn cấu hình thay vì hard-code |

Đọc qua `pydantic-settings` trong `config.py`. Có `.env.example` làm mẫu, không chứa giá trị thật. Không commit `.env`.

## Khả năng mở rộng

Phạm vi mục tiêu: vài chục–vài trăm người dùng đồng thời (quy mô đồ án/triển khai nhỏ), không phải enterprise scale.

- **SQLite WAL mode**: bật `PRAGMA journal_mode=WAL` + `PRAGMA synchronous=NORMAL` khi tạo engine trong `database.py` — cho phép nhiều reader đọc đồng thời với 1 writer (giải thích: write-ahead log thay vì rollback journal)
- **Session/connection**: 1 SQLAlchemy session/request qua FastAPI `Depends(get_db)`, `expire_on_commit=False`; `check_same_thread=False` cho SQLite
- **Cache**: cache embedding của câu hỏi lặp lại (LRU theo câu hỏi đã chuẩn hoá) để giảm gọi Gemini API; cache kết quả Chroma query với TTL ngắn cho câu hỏi giống hệt — quan trọng hơn trước vì Gemini embedding free tier có giới hạn quota (request/phút), khác với Ollama chạy local không giới hạn
- **Async I/O**: endpoint FastAPI dùng `async def`; các lời gọi blocking (`embedding.embed_query`, Chroma query, Groq API) chạy qua threadpool (`run_in_threadpool`) để không chặn event loop
- **Stateless backend**: không giữ state trong bộ nhớ server ngoài cookie + DB → dễ scale ngang hoặc chuyển sang PostgreSQL sau này mà không đổi kiến trúc
- **Phân trang**: bắt buộc cho mọi danh sách (hội thoại, tin nhắn, quiz) — xem [algorithms.md](algorithms.md) mục 4
- **Ingest nền**: `ingest.py` chạy như background task (`BackgroundTasks` hoặc bảng `jobs` đơn giản) thay vì block request, vì xử lý PDF + embedding chậm

## Sao lưu (backup)

- **SQLite**: `scripts/backup_db.py` dùng Online Backup API (`sqlite3.Connection.backup()`) — snapshot nhất quán kể cả khi app đang chạy, an toàn hơn copy file trực tiếp
- **Chroma**: copy/zip thư mục `chroma_db/` cùng lịch chạy — **không** backup khi đang chạy `ingest.py` (tránh state nửa vời)
- **Lịch chạy**: định kỳ qua Task Scheduler (Windows) hoặc cron, đặt tên file timestamp `backups/app_YYYYMMDD_HHMMSS.db`
- **Retention** (thuật toán xoay vòng theo tầng): giữ N bản gần nhất theo ngày (vd 14) + M bản theo tuần (vd 4), xoá bản cũ hơn — chạy trong cùng script sau khi backup xong

## Khôi phục (restore)

`scripts/restore_db.py <backup_file>` — quy trình:
1. Dừng ứng dụng (app phải tắt để tránh ghi đè khi đang phục hồi)
2. Sao lưu an toàn bản hiện tại (`data/app.db` → `data/app.db.before_restore`) — phòng trường hợp chọn nhầm file
3. Copy file backup đã chọn đè lên `data/app.db`
4. Khởi động lại ứng dụng, kiểm tra dữ liệu

Ghi quy trình này thành runbook từng bước trong phụ lục báo cáo — minh chứng cho phần "khả năng phục hồi sau sự cố".

## Triển khai Docker / VPS

Ứng dụng đóng gói bằng `Dockerfile` (python:3.12-slim), chạy cùng `docker-compose.yml` gồm 2 service:
- `app`: FastAPI/Uvicorn, chỉ expose nội bộ port 8000
- `caddy`: reverse proxy, mở port 80/443, tự xin chứng chỉ HTTPS (Let's Encrypt)

Dữ liệu (`data/`, `chroma_db/`, `backups/`) được bind-mount từ host vào container nên **không mất khi rebuild**.

### 1. Build & chạy local (kiểm thử trước khi lên VPS)

```
docker compose up --build
```

Truy cập `http://localhost` (qua Caddy, port 80). `Caddyfile` mặc định dùng `localhost` (HTTP, không cần chứng chỉ) cho môi trường dev.

### 2. Chuẩn bị VPS Ubuntu

```
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # rồi đăng nhập lại để áp dụng group
```

### 3. Đưa code lên VPS

Dùng `scp -r` hoặc `rsync` (loại trừ `venv/` — xem `.gitignore`/`.dockerignore`):

```
rsync -avz --exclude venv --exclude __pycache__ --exclude .pytest_cache \
  ./ user@<vps-ip>:/opt/chatbot-c/
```

### 4. Tạo `.env` thật trên VPS (không commit)

Sao chép `.env.example` → `.env`, điền:
- `GROQ_API_KEY`, `GOOGLE_API_KEY` — copy từ máy local hoặc tạo key mới
- `SECRET_KEY` — sinh mới: `python -c "import secrets; print(secrets.token_hex(32))"`
- `SESSION_HTTPS_ONLY=true` — bắt buộc trên VPS vì Caddy phục vụ qua HTTPS

### 5. Đảm bảo có dữ liệu trước lần build đầu tiên

Copy `data/app.db` và `chroma_db/` đã có sẵn từ máy local (đã chạy `ingest.py` + `seed_quizzes.py`) lên VPS, vào đúng thư mục sẽ bind-mount (`/opt/chatbot-c/data/`, `/opt/chatbot-c/chroma_db/`). Nếu không, volume rỗng sẽ che mất dữ liệu trong image.

### 6. Lấy IP VPS, sửa `Caddyfile`

```
curl -4 ifconfig.me
```

Sửa `Caddyfile` thành:

```
<vps-ip>.sslip.io {
    reverse_proxy app:8000
}
```

`sslip.io` cho phép `<ip>.sslip.io` tự resolve về IP đó — không cần mua domain, Caddy tự xin chứng chỉ Let's Encrypt cho hostname này.

### 7. Mở firewall

```
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 8. Chạy

```
docker compose up -d --build
```

### 9. Kiểm tra

Truy cập `https://<vps-ip>.sslip.io` — đăng ký/đăng nhập/chat/quiz phải hoạt động đầy đủ qua HTTPS.

### Cập nhật code sau này

```
rsync -avz --exclude venv --exclude __pycache__ --exclude .pytest_cache ./ user@<vps-ip>:/opt/chatbot-c/
ssh user@<vps-ip> "cd /opt/chatbot-c && docker compose up -d --build"
```

Volumes giữ nguyên dữ liệu (`data/`, `chroma_db/`, `backups/`) qua các lần rebuild.

### Backup định kỳ trên VPS

Thêm vào crontab:

```
0 2 * * * cd /opt/chatbot-c && docker compose exec -T app python scripts/backup_db.py --with-chroma
```
