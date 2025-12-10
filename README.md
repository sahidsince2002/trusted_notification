# Trusted Notifications System

**Author:** sahidsince2002  
**Last Updated:** 2025-12-10

> A reliable, safe, and timely notification delivery platform with intelligent routing, spam filtering, and comprehensive retry mechanisms.

## Overview

The **Trusted Notifications System** is an enterprise-grade notification delivery platform designed to ensure reliable message delivery across multiple channels (Email, SMS, Push, WhatsApp) with policy-based routing, intelligent escalation, and built-in safety mechanisms.

### Key Features

✅ **Multi-Channel Delivery** - Email, SMS, Push Notifications, WhatsApp  
✅ **Policy-Based Routing** - Configurable delivery rules per event type  
✅ **Intelligent Retry Logic** - Automatic retries with configurable backoff  
✅ **Spam Detection** - Built-in spam filtering mechanism  
✅ **Escalation Chains** - Automatic escalation for critical failures  
✅ **Idempotency Support** - Prevents duplicate notifications  
✅ **Delivery Tracking** - Comprehensive attempt logs and analytics  
✅ **RESTful API** - Easy integration with external systems  
✅ **Interactive Dashboard** - Real-time monitoring and policy management  

---

## 📁 Project Structure

```
trusted_notification/
├── app.py                          # Flask application & API endpoints
├── notifications.py                # Core notification processing logic
├── rules_engine.py                 # Policy extraction from master sheet
├── workers.py                      # Channel dispatcher & provider integration
├── db.py                           # SQLite database management
├── spam_filter.py                  # Spam detection mechanism
├── utils.py                        # Utility functions (ID generation, etc.)
├── master_sheet.csv                # Policy configuration
├── requirements.txt                # Python dependencies
├── notifications.db                # SQLite database (auto-generated)
│
├── channels/                       # Channel-specific providers
│   ├── __init__.py
│   ├── email.py                   # Email provider mock
│   ├── sms.py                     # SMS provider mock
│   ├── push.py                    # Push notification provider mock
│   ├── whatsapp.py                # WhatsApp provider mock
│   └── __pycache__/
│
├── templates/
│   └── dashboard.html              # Web dashboard UI
│
├── static/
│   └── app.js                      # Frontend JavaScript
│
└── __pycache__/
```

---

## 🏗️ Architecture

<img width="3084" height="3564" alt="image" src="https://github.com/user-attachments/assets/f786a757-748b-4b97-b795-0e745c81de5b" />


> Note: GitHub renders Mermaid diagrams in many previews and in the web UI when enabled; otherwise the block appears as code.

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **app.py** | Flask server, REST API endpoints, dashboard serving |
| **notifications.py** | Core logic: idempotency, spam filtering, channel execution, escalation |
| **rules_engine.py** | Parses CSV policies, determines retry logic, classifies criticality |
| **workers.py** | Dispatcher pattern, interfaces with channel providers |
| **channels/** | Mock implementations of Email, SMS, Push, WhatsApp providers |
| **db.py** | SQLite schema, CRUD operations, thread-safe access |
| **spam_filter.py** | Keyword-based spam detection |
| **utils.py** | Event ID generation, utility helpers |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd trusted_notification
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```powershell
   python app.py
   ```

4. **Access the dashboard:**
   - Open browser: `http://localhost:5000`

### Runnable example (curl)

Send a sample password-reset event using `curl` (replace host if different):

```bash
curl -s -X POST http://localhost:5000/api/send \
  -H "Content-Type: application/json" \
  -d '{
	"event_type": "password_reset",
	"payload": { "user_id": "usr_001", "email": "user@example.com" },
	"idempotency_key": "idem_abc123"
  }'

# Expected: 202 Accepted + JSON body with event_id and status PROCESSING
```

---

## 📚 Core Modules

### 1. **notifications.py** - Event Processing Pipeline

Handles the complete notification lifecycle:

```python
def send_event(event_type, payload, idempotency_key=None):
	"""
	Main entry point for sending notifications.
    
	Steps:
	1. Check idempotency (prevent duplicates)
	2. Spam filter check
	3. Load policy from rules engine
	4. Execute channel strategies (sequential/parallel)
	5. Trigger escalation if needed
	"""
```

**Key Functions:**
- `send_event()` - Main entry point
- `process_event()` - Executes delivery strategy
- `execute_channel()` - Single channel with retries
- `execute_escalation_chain()` - Escalation handling

### 2. **rules_engine.py** - Policy Management

Extracts notification rules from `master_sheet.csv`:

```python
POLICIES = {
	"password_reset": {
		"channels": [
			{"name": "EMAIL", "max_attempts": 3, "wait_for": 5, "success_rate": 95.0}
		],
		"delivery_mode": "SEQUENTIAL",
		"criticality": "HIGH"
	},
}
```

### 3. **workers.py** - Channel Dispatcher

Abstracts provider interfaces with configurable success rates:

```python
result = dispatcher.send_to_provider(
	channel="EMAIL",
	payload={"to": "user@example.com", "subject": "..."},
	configured_rate=95.0
)
```

### 4. **db.py** - Data Persistence

Three main tables: `events`, `attempts`, `secure_inbox`, `idempotency`.

---

## 🔌 API Reference

### **POST /api/send** - Send Notification

Send a notification through configured channels.

**Request:**
```json
{
	"event_type": "password_reset",
	"payload": { "user_id": "usr_123", "email": "user@example.com" },
	"idempotency_key": "idem_xyz789"
}
```

**Response (202 Accepted):**
```json
{
	"event_id": "evt_1234567890",
	"status": "PROCESSING",
	"event_type": "password_reset"
}
```

---

## ⚙️ Configuration

### Master Sheet (master_sheet.csv)

Define policies with columns:

```csv
Event Type, Category, Priority, Channels, Delivery Mode, Max Attempts, Wait For (seconds), Criticality, Risk, Retry %, Success Rate (%)
password_reset, Authentication, 8, Email, Sequential, 3, 5, High, Low, 50, 95.0
```

### Environment Variables

Create `.env` file:
```powershell
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///notifications.db
PROVIDER_TIMEOUT=10
```

---

## 🔒 Safety Mechanisms

### 1. **Idempotency**
Prevents duplicate notifications using idempotency keys.

### 2. **Spam Filtering**
Detects and blocks spam notifications.

### 3. **Escalation Chains**
Automatic escalation for critical failures.

### 4. **Thread Safety**
SQLite operations protected by locks.

---

## 📊 Delivery Strategies

### Sequential Delivery

Channels tried one-by-one until one succeeds.

### Parallel Delivery

All channels attempted simultaneously.

---

## 🧪 Example Workflows

### Workflow 1: Password Reset (Sequential)

Workflow: POST /api/send -> idempotency -> spam filter -> policy -> EMAIL -> SUCCESS

---

## 🛠️ Development

### Adding a New Channel

1. Create a provider mock in `channels/` and register it in `workers.py`.

### Real provider examples (illustrative)

SendGrid (Email) example (illustrative only — do not embed credentials):

```python
import requests

def send_with_sendgrid(api_key, to_email, subject, content):
	url = "https://api.sendgrid.com/v3/mail/send"
	headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
	payload = {
		"personalizations": [{"to": [{"email": to_email}]}],
		"from": {"email": "no-reply@yourdomain.com"},
		"subject": subject,
		"content": [{"type": "text/plain", "value": content}]
	}
	r = requests.post(url, json=payload, headers=headers, timeout=10)
	return {"status": "DELIVERED" if r.status_code in (200,202) else "FAILED", "code": r.status_code}
```

Twilio (SMS) example (illustrative):

```python
from twilio.rest import Client

def send_with_twilio(account_sid, auth_token, to, body, from_number):
	client = Client(account_sid, auth_token)
	msg = client.messages.create(body=body, from_=from_number, to=to)
	return {"status": "DELIVERED" if msg.status in ("sent","delivered") else "FAILED", "sid": msg.sid}
```

Add a note that these require real credentials and network access, and that production usage should handle errors, rate limits, and retries.

---

## 📐 Exporting Diagrams

If you want PNG/SVG exports of the Mermaid diagram locally, install `mmdc` (Mermaid CLI) or use Docker:

Using npm (mmdc):
```bash
npm i -g @mermaid-js/mermaid-cli
mmdc -i diagram.mmd -o diagram.png
```

Using Docker:
```bash
docker run --rm -v "$PWD":/data minlag/mermaid-cli -i diagram.mmd -o diagram.png
```

Create `diagram.mmd` containing the Mermaid block from above then run the commands to export.

---

## 📈 Monitoring & Analytics

Key metrics and simple SQL queries to inspect attempts and channel performance.

---

## 🐛 Troubleshooting

Common issues and solutions (DB locks, missing idempotency, provider failures).

---

## 📝 Dependencies

```
Flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
```

---

## 👥 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit a Pull Request

---

## 🎯 Future Enhancements

- [ ] PostgreSQL/MySQL support
- [ ] Message queue integration (Celery/RabbitMQ)
- [ ] Advanced analytics dashboard
- [ ] Real provider integrations (SendGrid, Twilio, etc.)

---

**Last Updated:** 2025-12-10  
**Repository:** trusted_notification  
**Branch:** submission

