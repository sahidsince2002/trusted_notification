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


https://github.com/user-attachments/assets/0608c81b-daf7-4e33-82f4-70c2f45fe47e



https://github.com/user-attachments/assets/9c5da074-7ad3-44bb-8f51-bbeab55088de


Filters: date, status, channel, search
<img width="1919" height="874" alt="Screenshot 2025-12-10 015523" src="https://github.com/user-attachments/assets/025b8b88-4914-4bc6-bcb3-c01d4cd84d90" />

Delivery Logs: complete attempt history
<img width="1623" height="848" alt="Screenshot 2025-12-10 015602" src="https://github.com/user-attachments/assets/aa995d82-d77d-4496-94a5-bc8ca133df82" />

Policy Manager: rendered from system rules
<img width="1650" height="530" alt="Screenshot 2025-12-09 235015" src="https://github.com/user-attachments/assets/f8aaf8a3-d417-4b67-8bcd-482d7250ccd8" />

Audit Trail: admin-level traceability
Built with HTML + CSS + JavaScript + Chart.js.


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

📄License

Made by Sahid Ahmed
Linkedin: https://www.linkedin.com/in/sahid-ahmed/
