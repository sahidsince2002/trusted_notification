🔔 Trusted Notification Delivery System

A policy-driven, multi-channel, fault-tolerant notification engine that simulates real-world delivery behavior across SMS, Email, Push, WhatsApp with retries, escalations, spam filtering, and analytics dashboard.

✅ Core Capabilities
📡 Multi-Channel Delivery

Supports:
SMS
Email
Push
WhatsApp
Escalation: Phone Call, Secure Inbox, Ops Alert

📘 Policy-Based Routing

Each event type defines:
Delivery Mode: Sequential / Parallel
Channels to attempt
Retries per channel
Escalation chain
Classification: Critical / High / Normal
Policies are auto-loaded and followed for every notification request.

🎲 Realistic Provider Simulation

Simulates real-world reliability using:
Configured provider success rate (from Master Sheet)
±5% runtime variation
Randomized delivery result based on effective probability

♻ Retry + Escalation Engine

Retries each channel according to its max_attempts
If all channels fail → escalation sequence triggers
All attempts are logged

🛡 Spam & Validation

Spam detection logic blocks harmful notifications
Validates required delivery fields based on policy channels
Rejects notifications with empty message or no valid contact

🗂 Idempotency

Duplicate requests (same idempotency key) return the original event ID.

📊 Live Dashboard (Frontend)

The web dashboard includes:
KPIs: total, delivered, failed, spam, success rate
Charts: channel usage, message volume, status breakdown
Filters: date, status, channel, search
Delivery Logs: complete attempt history
Policy Manager: rendered from system rules
Audit Trail: admin-level traceability
Built with HTML + CSS + JavaScript + Chart.js.



https://github.com/user-attachments/assets/cbeeff7f-c653-4705-a0fe-961495a88de9



https://github.com/user-attachments/assets/448f9699-baab-44af-ba35-4512c4e1f370




📚 File Structure

trusted_notification/
│
├── app.py                # Flask server
├── notifications.py      # Core notification engine
├── rules_engine.py       # Policy manager
├── workers.py            # Provider simulation engine
├── spam_filter.py        # Spam logic
├── db.py                 # SQLite event/log storage
├── utils.py              # Helper utilities
│
├── channels/             # Channel providers
│   ├── sms.py
│   ├── email.py
│   ├── push.py
│   └── whatsapp.py
│
├── static/
│   └── app.js            # Dashboard logic + charts + filters
│
├── templates/
│   └── dash.html         # Complete dashboard UI
│
└── README.md

🚀 Run Locally
git clone <repo_url>
cd trusted-notification-system

python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
python app.py


Dashboard opens at:
👉 http://127.0.0.1:5000

📥 Send Notification (Example)

POST /api/send

{
  "event_type": "BENEFICIARY ADDED ALERT",
  "payload": {
    "to": "9876543210",
    "message": "A new beneficiary was added to your account."
  }
}


Response

{
  "status": "ACCEPTED",
  "event_id": "f32a9db1-25c4-4a5b-b7f3-6ea820a3c447"
}

🧪 Delivery Simulation Example
{
  "status": "FAILED",
  "provider_response": { "status": "DELIVERED" },
  "configured_provider_rate": 47.86,
  "effective_rate": 44.68
}

📌 Key Highlights

Fully functional retry + escalation engine
Realistic provider behavior using probability
Interactive dashboard for monitoring
Cleanly separated backend logic
Enterprise-style design for system reliability
