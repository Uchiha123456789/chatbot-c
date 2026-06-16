const conversationListEl = document.getElementById("conversation-list");
const newConversationBtn = document.getElementById("new-conversation");
const logoutForm = document.getElementById("logout-form");
const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("ask-form");
const inputEl = document.getElementById("question");

let conversations = [];
let currentConversationId = null;

function renderMarkdown(content) {
    const html = marked.parse(content, { breaks: true });
    return DOMPurify.sanitize(html);
}

function addCodeCopyButtons(container) {
    for (const pre of container.querySelectorAll("pre")) {
        if (pre.querySelector(".code-copy-btn")) continue;
        const code = pre.querySelector("code");
        if (!code) continue;

        pre.style.position = "relative";
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "code-copy-btn";
        btn.textContent = "Sao chép";
        btn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(code.textContent);
                btn.textContent = "Đã chép!";
            } catch {
                btn.textContent = "Không thể chép";
            }
            setTimeout(() => { btn.textContent = "Sao chép"; }, 1500);
        });
        pre.appendChild(btn);
    }
}

function setMarkdownContent(bodyEl, content) {
    bodyEl.innerHTML = renderMarkdown(content);
    addCodeCopyButtons(bodyEl);
}

function buildFeedbackBar(messageId) {
    const bar = document.createElement("div");
    bar.className = "feedback-bar";
    const state = { rating: null };

    const likeBtn = document.createElement("button");
    likeBtn.type = "button";
    likeBtn.className = "feedback-btn";
    likeBtn.textContent = "👍";
    likeBtn.title = "Câu trả lời hữu ích";

    const dislikeBtn = document.createElement("button");
    dislikeBtn.type = "button";
    dislikeBtn.className = "feedback-btn";
    dislikeBtn.textContent = "👎";
    dislikeBtn.title = "Câu trả lời chưa tốt";

    const commentToggle = document.createElement("button");
    commentToggle.type = "button";
    commentToggle.className = "feedback-btn";
    commentToggle.textContent = "💬";
    commentToggle.title = "Thêm nhận xét";

    const commentBox = document.createElement("div");
    commentBox.className = "feedback-comment-box hidden";
    const commentInput = document.createElement("input");
    commentInput.type = "text";
    commentInput.placeholder = "Nhận xét của bạn (tuỳ chọn)...";
    commentInput.maxLength = 1000;
    const commentSend = document.createElement("button");
    commentSend.type = "button";
    commentSend.textContent = "Gửi";
    commentBox.append(commentInput, commentSend);

    function updateActiveStyles() {
        likeBtn.classList.toggle("active", state.rating === 1);
        dislikeBtn.classList.toggle("active", state.rating === -1);
    }

    async function sendFeedback(rating, comment) {
        if (rating === null) {
            await apiFetch(`/api/messages/${messageId}/feedback`, { method: "DELETE" });
        } else {
            await apiFetch(`/api/messages/${messageId}/feedback`, {
                method: "PUT",
                body: JSON.stringify({ rating, comment: comment || null }),
            });
        }
        state.rating = rating;
        updateActiveStyles();
    }

    likeBtn.addEventListener("click", () => {
        const next = state.rating === 1 ? null : 1;
        sendFeedback(next, commentInput.value.trim()).catch((err) => console.error(err));
    });
    dislikeBtn.addEventListener("click", () => {
        const next = state.rating === -1 ? null : -1;
        sendFeedback(next, commentInput.value.trim()).catch((err) => console.error(err));
    });
    commentToggle.addEventListener("click", () => {
        commentBox.classList.toggle("hidden");
        if (!commentBox.classList.contains("hidden")) commentInput.focus();
    });
    commentSend.addEventListener("click", () => {
        const rating = state.rating ?? 1;
        sendFeedback(rating, commentInput.value.trim()).catch((err) => console.error(err));
        commentBox.classList.add("hidden");
    });

    bar.append(likeBtn, dislikeBtn, commentToggle, commentBox);
    return bar;
}

function appendMessage({ id = null, role, content }) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;

    const body = document.createElement("div");
    body.className = "message-body";
    if (role === "assistant") {
        setMarkdownContent(body, content);
    } else {
        body.textContent = content;
    }
    wrapper.appendChild(body);

    if (role === "assistant" && id !== null) {
        wrapper.appendChild(buildFeedbackBar(id));
    }

    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return { wrapper, body };
}

function renderConversationList() {
    conversationListEl.innerHTML = "";
    for (const conv of conversations) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "conversation-item" + (conv.id === currentConversationId ? " active" : "");
        item.textContent = conv.title;
        item.addEventListener("click", () => selectConversation(conv.id));
        conversationListEl.appendChild(item);
    }
}

async function loadConversations() {
    conversations = await apiFetch("/api/conversations");
    renderConversationList();
    if (conversations.length === 0) {
        await createConversation();
    } else if (currentConversationId === null) {
        await selectConversation(conversations[0].id);
    }
}

async function createConversation() {
    const conv = await apiFetch("/api/conversations", { method: "POST", body: JSON.stringify({}) });
    conversations.unshift(conv);
    await selectConversation(conv.id);
    renderConversationList();
}

async function selectConversation(conversationId) {
    currentConversationId = conversationId;
    renderConversationList();
    messagesEl.innerHTML = "";

    const messages = await apiFetch(`/api/conversations/${conversationId}/messages`);
    for (const msg of messages) {
        appendMessage({ id: msg.id, role: msg.role, content: msg.content });
    }
    inputEl.focus();
}

newConversationBtn.addEventListener("click", () => {
    createConversation().catch((err) => console.error(err));
});

logoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await apiFetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
});

formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = inputEl.value.trim();
    if (!question || currentConversationId === null) return;

    appendMessage({ role: "user", content: question });
    inputEl.value = "";
    inputEl.disabled = true;
    formEl.querySelector("button").disabled = true;

    const thinking = appendMessage({ role: "assistant", content: "Đang suy nghĩ..." });

    try {
        const data = await apiFetch("/api/ask", {
            method: "POST",
            body: JSON.stringify({ conversation_id: currentConversationId, question }),
        });
        setMarkdownContent(thinking.body, data.answer);
        thinking.wrapper.appendChild(buildFeedbackBar(data.assistant_message_id));

        const conv = conversations.find((c) => c.id === currentConversationId);
        if (conv && conv.title === "Cuộc trò chuyện mới") {
            conv.title = question.slice(0, 60);
            renderConversationList();
        }
    } catch (err) {
        thinking.body.textContent = "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.";
        console.error(err);
    } finally {
        inputEl.disabled = false;
        formEl.querySelector("button").disabled = false;
        inputEl.focus();
    }
});

loadConversations().catch((err) => console.error(err));
