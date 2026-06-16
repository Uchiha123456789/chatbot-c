const topicSelect = document.getElementById("topic-select");
const quizListEl = document.getElementById("quiz-list");
const quizPickerEl = document.getElementById("quiz-picker");
const quizRunnerEl = document.getElementById("quiz-runner");
const quizTitleEl = document.getElementById("quiz-title");
const quizFormEl = document.getElementById("quiz-form");
const quizResultEl = document.getElementById("quiz-result");
const backToListBtn = document.getElementById("back-to-list");
const logoutForm = document.getElementById("logout-form");

const QUESTION_TYPE_LABELS = {
    mcq: "Trắc nghiệm",
    short_answer: "Tự luận ngắn",
    code: "Viết code",
};

function renderMarkdown(content) {
    return DOMPurify.sanitize(marked.parse(content, { breaks: true }));
}

function showPicker() {
    quizPickerEl.classList.remove("hidden");
    quizRunnerEl.classList.add("hidden");
    quizResultEl.classList.add("hidden");
    quizResultEl.innerHTML = "";
}

function showRunner() {
    quizPickerEl.classList.add("hidden");
    quizRunnerEl.classList.remove("hidden");
    quizResultEl.classList.add("hidden");
}

async function loadTopics() {
    const topics = await apiFetch("/api/topics");
    for (const topic of topics) {
        const option = document.createElement("option");
        option.value = topic.id;
        option.textContent = topic.name;
        topicSelect.appendChild(option);
    }
}

async function loadQuizzes() {
    const topicId = topicSelect.value;
    const url = topicId ? `/api/quizzes?topic_id=${encodeURIComponent(topicId)}` : "/api/quizzes";
    const quizzes = await apiFetch(url);

    quizListEl.innerHTML = "";
    if (quizzes.length === 0) {
        quizListEl.innerHTML = '<p class="caption">Chưa có bài quiz nào cho lựa chọn này.</p>';
        return;
    }
    for (const quiz of quizzes) {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "quiz-card";
        card.innerHTML = `<strong>${escapeHtml(quiz.title)}</strong><span>${quiz.question_count} câu hỏi</span>`;
        card.addEventListener("click", () => startQuiz(quiz.id));
        quizListEl.appendChild(card);
    }
}

async function startQuiz(quizId) {
    const quiz = await apiFetch(`/api/quizzes/${quizId}`);
    quizTitleEl.textContent = quiz.title;
    quizFormEl.innerHTML = "";
    quizFormEl.dataset.quizId = quiz.id;

    quiz.questions.forEach((question, index) => {
        const fieldset = document.createElement("fieldset");
        fieldset.className = "quiz-question";
        fieldset.dataset.questionId = question.id;

        const legend = document.createElement("legend");
        legend.innerHTML = `<span class="quiz-question-type">${QUESTION_TYPE_LABELS[question.question_type] || question.question_type}</span>
            Câu ${index + 1}: ${renderMarkdown(question.prompt)}`;
        fieldset.appendChild(legend);

        let input;
        if (question.question_type === "code") {
            input = document.createElement("textarea");
            input.rows = 6;
            input.placeholder = "Nhập đoạn code C của bạn...";
            input.spellcheck = false;
            input.className = "quiz-code-input";
        } else if (question.question_type === "mcq") {
            input = document.createElement("input");
            input.type = "text";
            input.placeholder = "Nhập đáp án...";
        } else {
            input = document.createElement("textarea");
            input.rows = 3;
            input.placeholder = "Nhập câu trả lời của bạn...";
        }
        input.required = true;
        input.maxLength = 4000;
        input.name = `answer-${question.id}`;
        fieldset.appendChild(input);

        quizFormEl.appendChild(fieldset);
    });

    const submitBtn = document.createElement("button");
    submitBtn.type = "submit";
    submitBtn.className = "quiz-submit-btn";
    submitBtn.textContent = "Nộp bài";
    quizFormEl.appendChild(submitBtn);

    showRunner();
}

quizFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const quizId = quizFormEl.dataset.quizId;
    const answers = [...quizFormEl.querySelectorAll(".quiz-question")].map((fieldset) => {
        const input = fieldset.querySelector("input, textarea");
        return { question_id: Number(fieldset.dataset.questionId), student_answer: input.value.trim() };
    });

    if (answers.some((a) => !a.student_answer)) {
        alert("Vui lòng trả lời tất cả các câu hỏi trước khi nộp bài.");
        return;
    }

    const submitBtn = quizFormEl.querySelector(".quiz-submit-btn");
    submitBtn.disabled = true;
    submitBtn.textContent = "Đang chấm điểm...";

    try {
        const result = await apiFetch(`/api/quizzes/${quizId}/attempt`, {
            method: "POST",
            body: JSON.stringify({ answers }),
        });
        renderResult(result);
    } catch (err) {
        alert(`Có lỗi khi nộp bài: ${err.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Nộp bài";
    }
});

function renderResult(result) {
    quizRunnerEl.classList.add("hidden");
    quizResultEl.classList.remove("hidden");

    const percent = Math.round((result.total_score || 0) * 100);
    let html = `<h2>Kết quả: ${percent}/100 điểm</h2>`;

    result.submissions.forEach((submission, index) => {
        const scorePercent = Math.round(submission.score * 100);
        html += `<div class="result-card">
            <div class="result-card-header">
                <span class="quiz-question-type">${QUESTION_TYPE_LABELS[submission.question_type] || submission.question_type}</span>
                <strong>Câu ${index + 1} — ${scorePercent}/100 điểm</strong>
            </div>
            <div class="result-prompt">${renderMarkdown(submission.prompt)}</div>
            <div class="result-answer"><strong>Câu trả lời của bạn:</strong> ${escapeHtml(submission.student_answer)}</div>
            ${renderGradingDetail(submission.grading_detail)}
        </div>`;
    });

    html += '<button type="button" class="link-btn" id="retry-btn">← Làm bài khác</button>';
    quizResultEl.innerHTML = html;
    document.getElementById("retry-btn").addEventListener("click", showPicker);
    quizResultEl.scrollIntoView({ behavior: "smooth" });
}

function renderGradingDetail(detail) {
    if (!detail || Object.keys(detail).length === 0) return "";
    const parts = [];

    if (detail.correct !== undefined) {
        parts.push(`<li>Đáp án đúng: <code>${escapeHtml(String(detail.expected ?? ""))}</code> — ${detail.correct ? "✅ chính xác" : "❌ chưa đúng"}</li>`);
    }
    if (detail.keywords) {
        parts.push(`<li>Từ khoá khớp: ${detail.keywords.matched.length}/${detail.keywords.expected.length}
            (${detail.keywords.matched.map(escapeHtml).join(", ") || "không có"})</li>`);
    }
    if (detail.embedding_similarity !== undefined) {
        parts.push(`<li>Độ tương đồng ngữ nghĩa với đáp án mẫu: ${Math.round(detail.embedding_similarity * 100)}%</li>`);
    }
    if (detail.structure) {
        parts.push(`<li>Cấu trúc bắt buộc: ${detail.structure.matched.length}/${detail.structure.required.length}
            — thiếu: ${detail.structure.missing.map(escapeHtml).join(", ") || "không"}</li>`);
    }
    if (detail.execution) {
        const ex = detail.execution;
        if (ex.ran) {
            parts.push(`<li>Đã biên dịch &amp; chạy thử — kết quả: <code>${escapeHtml(ex.stdout || "")}</code>
                ${ex.output_matches !== undefined ? (ex.output_matches ? "✅ khớp kỳ vọng" : "❌ chưa khớp kỳ vọng") : ""}</li>`);
        } else {
            parts.push(`<li>Không chạy thử được: ${escapeHtml(ex.reason || "")}</li>`);
        }
    }

    if (parts.length === 0) return "";
    return `<ul class="result-detail">${parts.join("")}</ul>`;
}

topicSelect.addEventListener("change", () => loadQuizzes().catch((err) => console.error(err)));
backToListBtn.addEventListener("click", showPicker);

logoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await apiFetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
});

Promise.all([loadTopics(), loadQuizzes()]).catch((err) => console.error(err));
