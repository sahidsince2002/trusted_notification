/* ==========================================================
   SEND EVENT
========================================================== */
async function sendEvent() {
    const event_type = document.getElementById("event_type").value;
    const phone = document.getElementById("phone").value.trim();
    const email = document.getElementById("email").value.trim();
    const device = document.getElementById("device").value.trim();
    const message = document.getElementById("message").value.trim();

    // -------------------------------
    // MANDATORY FIELD VALIDATION
    // -------------------------------

    if (!message) {
        alert("Message cannot be empty.");
        return;
    }

    // Fetch policy for this event type
    const policies = await loadPolicies();
    const policy = policies[event_type];

    const channels = policy.channels.map(c => c.name);

    // If SMS is part of policy → phone is required
    if (channels.includes("SMS") && !phone) {
        alert("Phone number is required for SMS delivery.");
        return;
    }

    // If EMAIL is part of policy → email is required
    if (channels.includes("EMAIL") && !email) {
        alert("Email address is required for Email delivery.");
        return;
    }

    // If PUSH is part of policy → device token is required
    if (channels.includes("PUSH") && !device) {
        alert("Device token is required for Push delivery.");
        return;
    }

    // -------------------------------
    // SEND PAYLOAD
    // -------------------------------

    const payload = {
        to: phone || null,
        email: email || null,
        device_token: device || null,
        message
    };

    let res = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_type, payload })
    });

    let json = await res.json();
    document.getElementById("send_result").innerText =
        JSON.stringify(json, null, 2);
}


/* ==========================================================
   LOAD EVENT TYPES
========================================================== */
async function loadPolicies() {
    const res = await fetch("/api/policies");
    return await res.json();
}

async function loadEventTypes() {
    const policies = await loadPolicies();
    const sel = document.getElementById("event_type");
    sel.innerHTML = "";

    Object.keys(policies).forEach(ev => {
        sel.innerHTML += `<option value="${ev}">${ev}</option>`;
    });
}

/* ==========================================================
   LOGS + FILTERS
========================================================== */
let cachedLogs = [];

async function loadGroupedLogs() {
    const res = await fetch("/api/logs");
    cachedLogs = await res.json();
    renderLogs();
}

function passesFilters(log) {
    const s = document.getElementById("filter_search").value.toLowerCase();
    const ch = document.getElementById("filter_channel").value;
    const st = document.getElementById("filter_status").value;
    const range = document.getElementById("filter_date").value;

    if (s.length > 0) {
        const text = (
            (log.event_id || "") +
            (log.channel || "") +
            (log.status || "") +
            (log.event_type || "")
        ).toLowerCase();
        if (!text.includes(s)) return false;
    }

    if (ch !== "ALL" && log.channel !== ch) return false;
    if (st !== "ALL" && log.status !== st) return false;

    const ts = new Date(log.timestamp + " UTC");
    const now = new Date();

    if (range === "1H" && now - ts > 3600e3) return false;
    if (range === "24H" && now - ts > 86_400e3) return false;
    if (range === "7D" && now - ts > 604_800e3) return false;

    return true;
}

/* ==========================================================
   RENDER LOGS WITH BADGE COLORS FIXED
========================================================== */
function renderLogs() {
    const logs = cachedLogs.filter(passesFilters);

    let html = `
        <table class="log-table">
            <thead>
                <tr>
                    <th>Event ID</th>
                    <th>Channel</th>
                    <th>Attempt</th>
                    <th>Status</th>
                    <th>Response</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
    `;

    logs.forEach(l => {
        let rowClass = "log-fail";

        if (l.status === "DELIVERED" || l.status === "SUCCESS")
            rowClass = "log-success";

        else if (l.status === "UNDELIVERED")
            rowClass = "log-retry";

        else if (l.status === "ESCALATION_TRIGGERED")
            rowClass = "log-escalation";

        let badgeClass = "badge-failed";

        if (l.status === "DELIVERED" || l.status === "SUCCESS")
            badgeClass = "badge-delivered";

        else if (l.status === "UNDELIVERED")
            badgeClass = "badge-retry";

        else if (l.status === "ESCALATION_TRIGGERED")
            badgeClass = "badge-escalation";

        else if (l.status === "SPAM_BLOCKED")
            badgeClass = "badge-spam";

        html += `
            <tr class="${rowClass}">
                <td>${l.event_id}</td>
                <td>${l.channel}</td>
                <td>#${l.attempt_no}</td>
                <td><span class="status-badge ${badgeClass}">
                        ${l.status}
                    </span>
                </td>
                <td>${l.response}</td>
                <td>${new Date(l.timestamp + " UTC")
                    .toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}
                </td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    document.getElementById("logs_grouped").innerHTML = html;
}

/* ==========================================================
   POLICY MANAGER TABLE
========================================================== */
async function loadPolicyManager() {
    let res = await fetch("/api/policies");
    let policies = await res.json();

    let html = "";

    Object.entries(policies).forEach(([event, cfg]) => {
        const classificationBadge =
            cfg.classification === "CRITICAL" ? "badge-critical" :
            cfg.classification === "HIGH" ? "badge-high" :
            "badge-normal";

        const modeBadge =
            cfg.delivery_mode === "PARALLEL" ? "badge-parallel" :
            "badge-sequential";

        const channelTags = cfg.channels
            .map(c => `<span class="channel-tag">${c.name}</span>`)
            .join("");

        const retryValues = cfg.channels
            .map(c => c.max_attempts)
            .join(", ");

        const escalationSteps = cfg.escalation.length
            ? cfg.escalation.map(e => `<span class="escalate-step">${e}</span>`).join("")
            : "—";

        html += `
            <tr>
                <td>${event}</td>
                <td><span class="${classificationBadge}">${cfg.classification}</span></td>
                <td><span class="${modeBadge}">${cfg.delivery_mode}</span></td>
                <td>${channelTags}</td>
                <td>${retryValues}</td>
                <td>${escalationSteps}</td>
            </tr>
        `;
    });

    document.getElementById("policy_table_body").innerHTML = html;
}

/* ==========================================================
   ANALYTICS — FULL RESTORE
========================================================== */
let channelChart = null;
let messageVolumeChart = null;
let statusChart = null;

async function loadAnalytics() {
    const res = await fetch("/api/logs");
    const logs = await res.json();

    const delivered = logs.filter(l => l.status === "DELIVERED" || l.status === "SUCCESS").length;
    const failed = logs.filter(l => l.status === "FAILURE" || l.status === "PERMANENT_FAILURE").length;
    const retry = logs.filter(l => l.status === "UNDELIVERED").length;
    const spam = logs.filter(l => l.status === "SPAM_BLOCKED").length;
    const total = logs.length;

    document.getElementById("kpi_total").innerText = total;
    document.getElementById("kpi_delivered").innerText = delivered;
    document.getElementById("kpi_failed").innerText = failed;
    document.getElementById("kpi_spam").innerText = spam;
    document.getElementById("kpi_success_rate").innerText =
        total ? ((delivered / total) * 100).toFixed(1) + "%" : "0%";

    const realLogs = logs.filter(l => l.channel !== "SPAM_FILTER");
    const sms = realLogs.filter(l => l.channel === "SMS").length;
    const email = realLogs.filter(l => l.channel === "EMAIL").length;
    const push = realLogs.filter(l => l.channel === "PUSH").length;

    updateChannelChart(sms, email, push);
    updateStatusChart(delivered, failed, retry, spam);

    const volumeMap = {};
    logs.forEach(l => {
        const et = l.event_type || "Unknown";
        volumeMap[et] = (volumeMap[et] || 0) + 1;
    });

    updateMessageVolumeChart(Object.keys(volumeMap), Object.values(volumeMap));
}

function updateChannelChart(sms, email, push) {
    const ctx = document.getElementById("channelChart");
    if (!ctx) return;

    if (channelChart) channelChart.destroy();

    channelChart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["SMS", "Email", "Push"],
            datasets: [{ data: [sms, email, push] }]
        },
        options: { plugins: { legend: { position: "bottom" } } }
    });
}

function updateMessageVolumeChart(labels, data) {
    const ctx = document.getElementById("messageVolumeChart");
    if (!ctx) return;

    if (messageVolumeChart) messageVolumeChart.destroy();

    messageVolumeChart = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label: "Messages Sent", data, borderWidth: 1 }] },
        options: { plugins: { legend: { display: false } }, indexAxis: "y" }
    });
}

function updateStatusChart(delivered, failed, retry, spam) {
    const ctx = document.getElementById("statusChart");
    if (!ctx) return;

    if (statusChart) statusChart.destroy();

    statusChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Delivered", "Failed", "Retries", "Spam"],
            datasets: [{ data: [delivered, failed, retry, spam], borderWidth: 1 }]
        },
        options: { plugins: { legend: { display: false } } }
    });
}

/* ==========================================================
   CLEAR LOGS BUTTON
========================================================== */
document.addEventListener("click", function (e) {
    if (e.target.id === "clearLogsBtn") {

        if (!confirm("Are you sure you want to delete all logs?")) return;

        fetch("/api/clear_logs", { method: "POST" })
            .then(res => res.json())
            .then(() => {
                alert("Logs cleared successfully!");
                loadGroupedLogs();  // Refresh table
                loadAnalytics();    // Refresh dashboard KPIs + charts
            })
            .catch(err => {
                console.error("Clear logs failed:", err);
                alert("Failed to clear logs.");
            });
    }
});

/* ==========================================================
   FILTER LISTENERS + AUTO REFRESH
========================================================== */
document.getElementById("filter_search").addEventListener("input", renderLogs);
document.getElementById("filter_channel").addEventListener("change", renderLogs);
document.getElementById("filter_status").addEventListener("change", renderLogs);
document.getElementById("filter_date").addEventListener("change", renderLogs);

setInterval(loadGroupedLogs, 3000);

document.addEventListener("DOMContentLoaded", () => {
    loadEventTypes();
    loadGroupedLogs();
});
