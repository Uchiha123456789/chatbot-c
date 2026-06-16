const masteryChartCanvas = document.getElementById("mastery-chart");
const masteryChartWrap = document.getElementById("mastery-chart-wrap");
const masteryEmptyEl = document.getElementById("mastery-empty");
const dueListEl = document.getElementById("due-list");
const tableBodyEl = document.getElementById("progress-table-body");
const logoutForm = document.getElementById("logout-form");

const dateFormatter = new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });

function formatDate(value) {
    if (!value) return "—";
    return dateFormatter.format(new Date(value));
}

function masteryColor(level) {
    if (level >= 0.7) return "#16a34a";
    if (level >= 0.4) return "#f59e0b";
    return "#dc2626";
}

function renderChart(topics) {
    if (topics.length === 0) {
        masteryChartWrap.classList.add("hidden");
        masteryEmptyEl.classList.remove("hidden");
        return;
    }
    masteryChartWrap.classList.remove("hidden");
    masteryEmptyEl.classList.add("hidden");

    new Chart(masteryChartCanvas, {
        type: "bar",
        data: {
            labels: topics.map((t) => t.topic_name),
            datasets: [{
                label: "Mức độ thành thạo (%)",
                data: topics.map((t) => Math.round(t.mastery_level * 100)),
                backgroundColor: topics.map((t) => masteryColor(t.mastery_level)),
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100, ticks: { callback: (v) => `${v}%` } },
            },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => `Thành thạo: ${ctx.parsed.y}%` } },
            },
        },
    });
}

function renderDueList(dueTopics) {
    if (dueTopics.length === 0) {
        dueListEl.innerHTML = '<p class="caption">🎉 Không có chủ đề nào cần ôn hôm nay — hãy thử làm thêm quiz ở chủ đề mới!</p>';
        return;
    }
    dueListEl.innerHTML = "";
    for (const topic of dueTopics) {
        const item = document.createElement("div");
        item.className = "due-item";
        item.innerHTML = `
            <div>
                <strong>${escapeHtml(topic.topic_name)}</strong>
                <span class="caption">Hạn ôn: ${formatDate(topic.next_review_at)} · thành thạo ${Math.round(topic.mastery_level * 100)}%</span>
            </div>
            <a class="link-btn" href="/quiz">Làm quiz ngay →</a>
        `;
        dueListEl.appendChild(item);
    }
}

function renderTable(topics) {
    tableBodyEl.innerHTML = "";
    if (topics.length === 0) {
        tableBodyEl.innerHTML = '<tr><td colspan="7" class="caption">Chưa có dữ liệu tiến độ.</td></tr>';
        return;
    }
    for (const topic of topics) {
        const row = document.createElement("tr");
        if (topic.is_due) row.classList.add("due-row");
        row.innerHTML = `
            <td>${escapeHtml(topic.topic_name)}</td>
            <td>${Math.round(topic.mastery_level * 100)}%</td>
            <td>${topic.ease_factor.toFixed(2)}</td>
            <td>${topic.interval_days}</td>
            <td>${topic.repetitions}</td>
            <td>${formatDate(topic.last_reviewed_at)}</td>
            <td>${formatDate(topic.next_review_at)}${topic.is_due ? ' <span class="due-badge">cần ôn</span>' : ""}</td>
        `;
        tableBodyEl.appendChild(row);
    }
}

async function loadDashboard() {
    const data = await apiFetch("/api/progress");
    renderChart(data.topics);
    renderDueList(data.due_today);
    renderTable(data.topics);
}

logoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await apiFetch("/auth/logout", { method: "POST" });
    window.location.href = "/login";
});

loadDashboard().catch((err) => console.error(err));
