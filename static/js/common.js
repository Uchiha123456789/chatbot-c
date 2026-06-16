/**
 * Helper gọi API JSON dùng chung. Cookie session tự gửi kèm (same-origin);
 * header X-Requested-With giúp phân biệt request API với điều hướng trang
 * thông thường (một lớp giảm thiểu CSRF nhẹ, theo docs/claude/security.md).
 */
async function apiFetch(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "fetch",
            ...(options.headers || {}),
        },
    });

    let data = null;
    const text = await res.text();
    if (text) {
        try { data = JSON.parse(text); } catch { data = null; }
    }

    if (!res.ok) {
        const message = (data && data.detail) ? data.detail : `Lỗi ${res.status}`;
        throw new Error(message);
    }
    return data;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
