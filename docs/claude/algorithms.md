# Cấu trúc dữ liệu & giải thuật

## 1. Pipeline RAG (truy xuất tăng cường)

**Hiện trạng** (`ingest.py`): chunking thuần đếm từ `chunk_text(text, chunk_size=300, overlap=30)` — sliding window theo số từ, không quan tâm ranh giới câu/khối code → dễ cắt giữa câu hoặc giữa đoạn code.

**Cải tiến đề xuất — chunking theo cấu trúc**:
1. Tách văn bản theo marker trang (`--- Page N ---`) và ranh giới đoạn văn trước
2. Chỉ áp dụng sliding window (300 từ / overlap 30) cho đoạn nào vượt `chunk_size`
3. Nhận diện khối code (dòng nhiều `{`, `;`, `#include`...) và giữ nguyên thành đơn vị atomic, không cắt giữa chừng

**Truy xuất**: Chroma dùng **HNSW** (Hierarchical Navigable Small World) — đồ thị phân lớp cho phép tìm kiếm xấp xỉ k láng giềng gần nhất (ANN) ở độ phức tạp ~O(log n) thay vì so sánh cosine vét cạn O(n). Giữ `n_results=3–5`. Có thể mở rộng bằng re-rank kết quả theo độ trùng từ khoá (kiểu BM25) để tăng độ chính xác (hybrid search) — ghi chú là hướng phát triển.

**Provenance**: mỗi câu trả lời lưu `messages.retrieved_chunk_ids` (id các chunk đã dùng) để truy vết & đánh giá chất lượng về sau.

## 2. Chấm điểm bài tập (grading_service)

Chiến lược **hybrid theo loại câu hỏi** (`question_type`):

| Loại | Cách chấm |
|---|---|
| `mcq` | So khớp chính xác đáp án với `reference_answer` |
| `short_answer` | So sánh từ khoá + độ tương đồng embedding: `cosine(embed(student_answer), embed(reference_answer))`, tái dùng `embedding.embed_query` đã có sẵn trong `rag_service` |
| `code` | Kiểm tra cấu trúc tĩnh trước (regex/heuristic tìm cấu trúc bắt buộc trong `grading_rubric`, vd phải có `for`, `printf`, đúng chữ ký hàm); **tuỳ chọn** biên dịch & chạy trong `subprocess.run(..., timeout=2, cwd=tempdir)` với giới hạn thời gian chặt, không mạng, dọn thư mục tạm — chỉ áp dụng cho snippet tự chứa đơn giản |

**Vì sao giới hạn phạm vi thực thi code**: chạy code C không tin cậy tiềm ẩn rủi ro bảo mật (arbitrary code execution). Với quy mô đồ án, ưu tiên kiểm tra cấu trúc tĩnh + so khớp output cho trường hợp đơn giản, có sandbox nghiêm ngặt; thực thi đầy đủ trong container cách ly (Docker/seccomp) ghi nhận là hướng mở rộng tương lai.

Mọi kết quả chấm (điểm + chi tiết từng tiêu chí) lưu vào `submissions.grading_detail` (JSON) để minh bạch và có thể tái kiểm tra.

## 3. Theo dõi tiến độ — SM-2 đơn giản hoá (progress_service)

Sau mỗi lần làm quiz, cập nhật trạng thái `(user, topic)` trong `topic_progress` theo thuật toán SM-2 (Wozniak) rút gọn:

```
quality q ∈ [0..5]   — suy ra từ điểm bài làm:
    score >= 0.9 → q=5 ; >= 0.7 → q=4 ; >= 0.5 → q=3 ; else → q thấp hơn

if q >= 3:
    if repetitions == 0:    interval = 1
    elif repetitions == 1:  interval = 6
    else:                   interval = round(interval * ease_factor)
    repetitions += 1
else:
    repetitions = 0
    interval = 1

ease_factor = max(1.3, ease_factor + (0.1 - (5-q) * (0.08 + (5-q) * 0.02)))
next_review_at = now + interval ngày

mastery_level = 0.7 * mastery_level + 0.3 * score   # exponential moving average
```

Mỗi `(user_id, topic_id)` là một state machine độc lập — dữ liệu để vẽ "lộ trình ôn tập" trên dashboard (`next_review_at` gần nhất → ưu tiên hiển thị "cần ôn hôm nay").

## 4. Phân trang & tải dữ liệu hiệu quả

- **Danh sách hội thoại**: cursor-based pagination `WHERE updated_at < :cursor ORDER BY updated_at DESC LIMIT :n` (dùng index `idx_conversations_user_updated`) — tránh chi phí `OFFSET` O(n) khi danh sách dài
- **Lịch sử tin nhắn**: tải N tin nhắn gần nhất (`ORDER BY created_at DESC LIMIT 30`), lazy-load thêm khi cuộn lên (infinite scroll) — vừa giữ UI mượt vừa giới hạn độ dài `history` gửi cho Groq (tránh vượt context window / tốn token)
