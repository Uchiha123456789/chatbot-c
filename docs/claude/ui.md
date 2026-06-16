# Giao diện (HTML/CSS/JS thuần)

Không dùng React/Vue hay bất kỳ build step nào — page shell render bằng Jinja2, phần động gọi REST JSON API qua `fetch()`. Thư viện ngoài (nếu cần) nhúng qua CDN `<script>` (vd Chart.js, marked.js, DOMPurify).

## Trang & layout

| Trang | Mô tả |
|---|---|
| `login.html` / `register.html` | Form căn giữa đơn giản, POST tới `/auth/login` / `/auth/register` |
| `chat.html` | 2 cột: **sidebar trái** = danh sách "project" hội thoại (nút "+ Cuộc trò chuyện mới", đổi tên/xoá qua modal nhỏ, gọi `/api/conversations`); **khung chính** = luồng tin nhắn + ô nhập + nút like/dislike trên mỗi tin nhắn assistant |
| `quiz.html` | Chọn chủ đề → danh sách câu hỏi → nộp bài → hiển thị kết quả chấm theo từng tiêu chí (`grading_detail`) |
| `dashboard.html` | Biểu đồ mastery theo chủ đề (Chart.js qua CDN), danh sách "cần ôn hôm nay" (`topic_progress.next_review_at`) |

`base.html` chứa header + sidebar dùng chung, các trang khác `{% extends "base.html" %}`.

## Giao tiếp với backend

- Toàn bộ thao tác động qua `fetch()` tới các endpoint `/api/...` (xem danh sách trong kế hoạch / `routers/`)
- `static/js/common.js`: helper dùng chung — gắn header, xử lý lỗi (toast thông báo), parse JSON response
- Mỗi trang có file JS riêng: `chat.js`, `auth.js`, `quiz.js`, `progress.js`

## Render Markdown an toàn

Câu trả lời assistant có thể chứa Markdown + code block. Luồng bắt buộc phía client:
```
raw markdown → marked.parse() → DOMPurify.sanitize() → element.innerHTML
```
Không bao giờ gán thẳng chuỗi chưa qua `DOMPurify.sanitize` vào `innerHTML` (xem [security.md](security.md) phần chống XSS).

## Style guide

- CSS thuần, biến màu khai báo trong `:root` (tông xanh-trắng nhẹ nhàng, phù hợp đối tượng sinh viên)
- Layout: flexbox/grid, có breakpoint responsive cho mobile
- Bong bóng chat bo góc, phân biệt rõ màu/canh lề giữa tin nhắn user và assistant
- Tổ chức CSS theo trang: `static/css/style.css` (chung/biến/`base`), `chat.css`, `quiz.css`,...
- Không kéo theo framework CSS nặng (Bootstrap/Tailwind) — giữ đúng tinh thần "thuần", có thể viết thêm `utilities.css` nhỏ nếu cần class lặp lại nhiều
