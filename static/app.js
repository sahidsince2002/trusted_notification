/* ==========================================================
   SEND EVENT
========================================================== */
async function sendEvent() {
    const event_type = document.getElementById("event_type").value;

    const payload = {
        to: document.getElementById("phone").value || null,
        email: document.getElementById("email").value || null,
        device_token: document.getElementById("device").value || null,
        message: document.getElementById("message").value || ""
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
   LOAD EVENT TYPES FROM POLICIES
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
   LOGS + FILTERING
========================================================== */
let cachedLogs = [];

async function loadGroupedLogs() {
    const res = await fetch("/api/logs");
    cachedLogs = await res.json();
    renderLogs();
}

/* ----- FILTER HELPERS ----- */
function passesFilters(log) {
    const s = document.getElementById("filter_search").value.toLowerCase();
    const ch = document.getElementById("filter_channel").value;
    const st = document.getElementById("filter_status").value;
    const range = document.getElementById("filter_date").value;

    // text search over event_id, channel, status, event_type
    if (s.length > 0) {
        const text = (
            (log.event_id || "") +
            (log.channel || "") +
            (log.status || "") +
            (log.event_type || "")
        ).toLowerCase();
        if (!text.includes(s)) return false;
    }

    // channel filter
    if (ch !== "ALL" && log.channel !== ch) return false;

    // status filter (DELIVERED / UNDELIVERED / PERMANENT_FAILURE / SPAM_BLOCKED)
    if (st !== "ALL" && log.status !== st) return false;

    // date range filter
    const ts = new Date(log.timestamp + " UTC");
    const now = new Date();

    if (range === "1H" && now - ts > 3600e3) return false;
    if (range === "24H" && now - ts > 86_400e3) return false;
    if (range === "7D" && now - ts > 604_800e3) return false;

    return true;
}

/* ==========================================================
   RENDER LOG TABLE
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
        let rowClass = "";
        if (l.status === "DELIVERED") rowClass = "log-success";
        else if (l.status === "UNDELIVERED") rowClass = "log-retry";
        else if (l.status === "SPAM_BLOCKED") rowClass = "log-spam";
        else rowClass = "log-fail";

        const statusBadgeClass =
            l.status === "DELIVERED" ? "badge-delivered" :
            l.status === "UNDELIVERED" ? "badge-unavailable" :
            l.status === "SPAM_BLOCKED" ? "badge-spam" :
            "badge-failed";

        html += `
            <tr class="log-row ${rowClass}">
                <td>${l.event_id}</td>

                <td>
                    <span class="channel-tag channel-${(l.channel || "").toLowerCase()}">
                        ${l.channel}
                    </span>
                </td>

                <td><span class="attempt-badge">#${l.attempt_no}</span></td>

                <td>
                    <span class="status-badge ${statusBadgeClass}">
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
   ANALYTICS (Dashboard Charts)
========================================================== */
let channelChart = null;
let statusChart = null;
let messageVolumeChart = null;

async function loadAnalytics() {
    const res = await fetch("/api/logs");
    const logs = await res.json();

    // KPIs (use all attempts; spam treated separately)
    const delivered = logs.filter(l => l.status === "DELIVERED").length;
    const failed = logs.filter(l =>
        l.status === "FAILED" || l.status === "PERMANENT_FAILURE"
    ).length;
    const retry = logs.filter(l => l.status === "UNDELIVERED").length;
    const spam = logs.filter(l => l.status === "SPAM_BLOCKED").length;
    const total = logs.length;

    document.getElementById("kpi_total").innerText = total;
    document.getElementById("kpi_delivered").innerText = delivered;
    document.getElementById("kpi_failed").innerText = failed;
    document.getElementById("kpi_spam").innerText = spam;
    document.getElementById("kpi_success_rate").innerText =
        total ? ((delivered / total) * 100).toFixed(1) + "%" : "0%";

    // Channel usage (exclude SPAM_FILTER pseudo-channel)
    const realLogs = logs.filter(l => l.channel !== "SPAM_FILTER");
    const sms = realLogs.filter(l => l.channel === "SMS").length;
    const email = realLogs.filter(l => l.channel === "EMAIL").length;
    const push = realLogs.filter(l => l.channel === "PUSH").length;

    updateChannelChart(sms, email, push);
    updateStatusChart(delivered, failed, retry, spam);

    // Message volume by event_type
    const volumeMap = {};
    logs.forEach(l => {
        const et = l.event_type || "Unknown";
        if (!volumeMap[et]) volumeMap[et] = 0;
        volumeMap[et]++;
    });

    const labels = Object.keys(volumeMap);
    const data = Object.values(volumeMap);

    updateMessageVolumeChart(labels, data);
}

/* ----- CHANNEL PIE ----- */
function updateChannelChart(sms, email, push) {
    const ctx = document.getElementById("channelChart");
    if (!ctx) return;

    if (channelChart) channelChart.destroy();

    channelChart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["SMS", "Email", "Push"],
            datasets: [{
                data: [sms, email, push]
            }]
        },
        options: {
            plugins: {
                legend: { position: "bottom" }
            }
        }
    });
}

/* ----- MESSAGE VOLUME BAR ----- */
function updateMessageVolumeChart(labels, data) {
    const ctx = document.getElementById("messageVolumeChart");
    if (!ctx) return;

    if (messageVolumeChart) messageVolumeChart.destroy();

    messageVolumeChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Messages Sent",
                data,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: "y", // horizontal bars for readability
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: { display: true, text: "Messages Sent" }
                },
                y: {
                    title: { display: true, text: "Event Type" }
                }
            }
        }
    });
}

/* ----- STATUS BAR ----- */
function updateStatusChart(delivered, failed, retry, spam) {
    const ctx = document.getElementById("statusChart");
    if (!ctx) return;

    if (statusChart) statusChart.destroy();

    statusChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Delivered", "Failed", "Retries", "Spam"],
            datasets: [{
                data: [delivered, failed, retry, spam],
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

/* ==========================================================
   LIVE FILTERS
========================================================== */
document.getElementById("filter_search").addEventListener("input", renderLogs);
document.getElementById("filter_channel").addEventListener("change", renderLogs);
document.getElementById("filter_status").addEventListener("change", renderLogs);
document.getElementById("filter_date").addEventListener("change", renderLogs);

/* ==========================================================
   AUTO REFRESH LOGS
========================================================== */
setInterval(loadGroupedLogs, 3000);

/* ==========================================================
   INITIAL LOAD
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
    loadEventTypes();
    loadGroupedLogs();
});

/* ==========================================================
   CLEAR LOGS
========================================================== */
document.addEventListener("click", function (e) {
    if (e.target.id === "clearLogsBtn") {
        if (!confirm("Are you sure you want to delete all logs?")) return;

        fetch("/api/clear_logs", { method: "POST" })
            .then(r => r.json())
            .then(() => {
                alert("Logs cleared!");
                loadGroupedLogs();
            });
    }
});



async function loadPolicyManager() {
    let res = await fetch("/api/policies");
    let policies = await res.json();

    let html = `<table class="log-table">
        <thead>
            <tr>
                <th>Event Type</th>
                <th>Classification</th>
                <th>Delivery Mode</th>
                <th>Channels</th>
                <th>Retries</th>
                <th>Escalation</th>
            </tr>
        </thead>
        <tbody>
    `;

    Object.entries(policies).forEach(([event, cfg]) => {
        html += `
            <tr>
                <td>${event}</td>
                <td>${cfg.classification}</td>
                <td>${cfg.delivery_mode}</td>
                <td>${cfg.channels.map(c => c.name).join(", ")}</td>
                <td>${cfg.channels.map(c => c.max_attempts).join(", ")}</td>
                <td>${cfg.escalation ? cfg.escalation.join(", ") : "None"}</td>
            </tr>
        `;
    });

    html += "</tbody></table>";

    document.getElementById("policy_list").innerHTML = html;
}


/* ==========================================================
   LOAD AUDIT TRAIL
========================================================== */
async function loadAuditTrail() {
    const container = document.getElementById("audit_container");
    if (!container) return;

    container.innerHTML = "Loading...";

    try {
        let res = await fetch("/api/audit");
        let logs = await res.json();

        if (!logs.length) {
            container.innerHTML = "<p>No audit events available.</p>";
            return;
        }

        let html = `
            <table class="log-table">
                <thead>
                    <tr>
                        <th>Event</th>
                        <th>Description</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
        `;

        logs.forEach(a => {
            html += `
                <tr>
                    <td>${a.event || "-"}</td>
                    <td>${a.message || "-"}</td>
                    <td>${a.timestamp || "-"}</td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        container.innerHTML = html;

    } catch (err) {
        container.innerHTML = "Failed to load audit logs.";
    }
}
