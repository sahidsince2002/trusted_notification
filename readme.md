# Trusted Notifications System

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

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    API Request (POST /api/send)              │
│            event_type, payload, idempotency_key              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  app.py (Flask)  │
                  │   Route Handler  │
                  └────────┬─────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  notifications.py      │
              │  send_event()          │
              └────────┬───────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
    ┌──────────────┐        ┌──────────────────┐
    │ Idempotency  │        │  Spam Filter     │
    │    Check     │        │  Detection       │
    └──────┬───────┘        └────────┬─────────┘
           │                         │
           └────────────┬────────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  rules_engine.py       │
            │ Get Policy for Event   │
            └────────┬───────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────────┐      ┌────────────┐
    │  Sequential  │      │  Parallel  │
    │  Delivery    │      │  Delivery  │
    └──────┬───────┘      └─────┬──────┘
           │                    │
    ┌──────┴────────────────────┴──────┐
    │                                  │
    ▼                                  ▼
┌─────────────────────────────────────────┐
│         workers.py (Dispatcher)          │
│   Route to Channel Providers             │
└──┬──────────┬──────────┬──────────┬─────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Email │ │ SMS  │ │ Push │ │WhatsApp  │
│Mock  │ │ Mock │ │ Mock │ │ Mock     │
└──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘
   │        │        │          │
   └────────┼────────┼──────────┘
            │        │
            ▼        ▼
    ┌──────────────────────┐
    │   db.py (SQLite)     │
    │  Log Attempts        │
    │  Track Status        │
    └──────────────────────┘
```

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
   ```bash
   git clone <repository-url>
   cd trusted_notification
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the dashboard:**
   - Open browser: `http://localhost:5000`

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
    "security_alert": {
        "channels": [
            {"name": "EMAIL", ...},
            {"name": "SMS", ...},
            {"name": "PUSH", ...}
        ],
        "delivery_mode": "PARALLEL",
        "criticality": "CRITICAL",
        "escalation": ["ADMIN_NOTIFICATION", "MANAGER_ALERT"]
    }
}
```

### 3. **workers.py** - Channel Dispatcher

Abstracts provider interfaces with configurable success rates:

```python
from workers import dispatcher

result = dispatcher.send_to_provider(
    channel="EMAIL",
    payload={"to": "user@example.com", "subject": "..."},
    configured_rate=95.0
)

# Returns:
# {
#     "status": "DELIVERED" | "FAILED" | "PERMANENT_FAILURE",
#     "configured_provider_rate": 95.0,
#     "effective_rate": 92.3,
#     "provider_response": {...}
# }
```

### 4. **db.py** - Data Persistence

Three main tables:

| Table | Purpose |
|-------|---------|
| `events` | Event metadata and status |
| `attempts` | Individual delivery attempts |
| `secure_inbox` | Payload storage |
| `idempotency` | Deduplication keys |

```python
# Example: Log attempt
log_attempt(
    event_id="evt_abc123",
    event_type="password_reset",
    channel="EMAIL",
    attempt_no=1,
    provider_response="{}",
    status="SUCCESS"
)
```

---

## 🔌 API Reference

### **POST /api/send** - Send Notification

Send a notification through configured channels.

**Request:**
```json
{
    "event_type": "password_reset",
    "payload": {
        "user_id": "usr_123",
        "email": "user@example.com",
        "reset_token": "token_abc"
    },
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

### **GET /api/policies** - Get All Policies

Retrieve configured notification policies.

**Response (200 OK):**
```json
{
    "password_reset": {...},
    "security_alert": {...},
    "order_confirmation": {...}
}
```

### **GET /api/logs** - Get Attempt Logs

Fetch delivery attempt history.

**Response (200 OK):**
```json
{
    "logs": [
        {
            "event_id": "evt_123",
            "event_type": "password_reset",
            "channel": "EMAIL",
            "attempt_no": 1,
            "status": "SUCCESS",
            "ts": "2024-01-15T10:30:45"
        }
    ]
}
```

### **DELETE /api/logs** - Clear Logs

Clear all attempt logs.

---

## ⚙️ Configuration

### Master Sheet (master_sheet.csv)

Define policies with columns:

```csv
Event Type, Category, Priority, Channels, Delivery Mode, Max Attempts, Wait For (seconds), Criticality, Risk, Retry %, Success Rate (%)
password_reset, Authentication, 8, Email, Sequential, 3, 5, High, Low, 50, 95.0
security_alert, Security, 9, Email→SMS→Push, Parallel, 2, 10, Critical, High, 75, 98.0
order_confirmation, Commerce, 6, Email→SMS, Sequential, 2, 5, Normal, Low, 40, 92.0
```

### Environment Variables

Create `.env` file:
```bash
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///notifications.db
PROVIDER_TIMEOUT=10
```

---

## 🔒 Safety Mechanisms

### 1. **Idempotency**
Prevents duplicate notifications using idempotency keys:

```python
# Same key always returns same result
send_event("password_reset", {...}, idempotency_key="idem_xyz")
send_event("password_reset", {...}, idempotency_key="idem_xyz")  # Duplicate prevented
```

### 2. **Spam Filtering**
Detects and blocks spam notifications:

```python
from spam_filter import is_spam_notification

if is_spam_notification(payload):
    # Block and log
    return {"status": "SPAM_DETECTED"}
```

### 3. **Escalation Chains**
Automatic escalation for critical failures:

```python
"escalation": ["ADMIN_NOTIFICATION", "MANAGER_ALERT", "CEO_NOTIFICATION"]
```

### 4. **Thread Safety**
SQLite operations protected by locks:

```python
_lock = threading.Lock()

with _lock:
    # Database operation
```

---

## 📊 Delivery Strategies

### Sequential Delivery
Channels tried one-by-one until one succeeds:

```python
"delivery_mode": "SEQUENTIAL",
"channels": [
    {"name": "EMAIL", "max_attempts": 3, "wait_for": 5},
    {"name": "SMS", "max_attempts": 2, "wait_for": 10}
]
```

### Parallel Delivery
All channels attempted simultaneously:

```python
"delivery_mode": "PARALLEL",
"channels": [
    {"name": "EMAIL", "max_attempts": 2},
    {"name": "PUSH", "max_attempts": 2},
    {"name": "SMS", "max_attempts": 1}
]
```

---

## 🧪 Example Workflows

### Workflow 1: Password Reset (Sequential)

```
User clicks "Reset Password"
        ↓
POST /api/send {event_type: "password_reset", ...}
        ↓
Check idempotency ✓
        ↓
Spam filter check ✓
        ↓
Load policy (Sequential, 3 attempts)
        ↓
Try EMAIL → Success
        ↓
Log SUCCESS
        ↓
Return 202 PROCESSING
```

### Workflow 2: Security Alert (Parallel + Escalation)

```
Suspicious login detected
        ↓
POST /api/send {event_type: "security_alert", ...}
        ↓
Idempotency & spam checks ✓
        ↓
Load policy (Parallel, CRITICAL)
        ↓
Attempt 3 channels simultaneously:
  - EMAIL → FAILED (retry 2) → SUCCESS ✓
  - SMS → SUCCESS ✓
  - PUSH → FAILED (max attempts) ✗
        ↓
At least one succeeded (EMAIL+SMS)
        ↓
Status: DELIVERED
        ↓
Log all attempts
```

---

## 🛠️ Development

### Adding a New Channel

1. **Create provider mock in `channels/`:**
   ```python
   # channels/telegram.py
   class TelegramProviderMock:
       def send(self, to, message, metadata):
           # Implement send logic
           return {"status": "DELIVERED"}
   
   telegram_provider = TelegramProviderMock()
   ```

2. **Register in `workers.py`:**
   ```python
   from channels.telegram import telegram_provider
   
   # Add to send_to_provider() method
   ```

3. **Add to CSV policies:**
   ```csv
   Event Type, ..., Channels, ...
   my_event, ..., Email→Telegram, ...
   ```

### Running Tests

```bash
python -m pytest tests/
```

### Debug Mode

```python
# In app.py
if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

---

## 📈 Monitoring & Analytics

### Key Metrics

- **Delivery Rate** - % of notifications successfully delivered
- **Retry Efficiency** - % of failures resolved on retry
- **Channel Performance** - Success rate per channel
- **Escalation Frequency** - How often escalation occurs
- **Spam Detection Rate** - % of spam blocked

### Access Logs

```bash
# Query all attempts for an event
SELECT * FROM attempts WHERE event_id = 'evt_123';

# Channel-wise statistics
SELECT channel, COUNT(*), 
       SUM(CASE WHEN status='SUCCESS' THEN 1 ELSE 0 END) as successes
FROM attempts
GROUP BY channel;
```

---

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Notifications not sending | Database locked | Check database file permissions |
| High failure rate | Provider issues | Adjust `success_rate` in CSV |
| Duplicate deliveries | Missing idempotency key | Always include `idempotency_key` |
| Escalations not triggered | Policy misconfigured | Verify `escalation` array in CSV |
| Spam false positives | Overly strict filter | Adjust keywords in `spam_filter.py` |

---

## 📝 Dependencies

```
Flask==2.3.3          # Web framework
requests==2.31.0      # HTTP client
python-dotenv==1.0.0  # Environment configuration
sqlite3               # Built-in database
```

For complete list, see `requirements.txt`.

---

## 📄 License

This project is part of a Capstone initiative focused on reliable notification delivery systems.

---

## 👥 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit a Pull Request

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue in the repository
- Contact: sahidsince2002

---

## 🎯 Future Enhancements

- [ ] PostgreSQL/MySQL support
- [ ] Message queue integration (Celery/RabbitMQ)
- [ ] Advanced analytics dashboard
- [ ] A/B testing for delivery channels
- [ ] ML-based optimal channel selection
- [ ] Real provider integrations (SendGrid, Twilio, etc.)
- [ ] WebSocket live notifications
- [ ] Rate limiting & throttling

---

**Last Updated:** December 2024  
**Repository:** trusted_notification  
**Branch:** submission
