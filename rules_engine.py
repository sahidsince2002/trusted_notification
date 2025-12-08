# rules_engine.py (FINAL COLUMN-CORRECT VERSION)
import csv

MASTER_CSV = "master_sheet.csv"

def normalize_channel(name: str):
    if not name:
        return None
    name = name.strip().lower()
    if "sms" in name: return "SMS"
    if "push" in name: return "PUSH"
    if "mail" in name or "email" in name: return "EMAIL"
    if "whatsapp" in name or "wa" in name: return "WHATSAPP"
    return name.upper()

def split_channels(raw_value):
    if not raw_value:
        return []
    cleaned = (
        raw_value.replace("→", ">")
                 .replace("->", ">")
                 .replace(",", ">")
                 .replace("/", ">")
    )
    parts = [p.strip() for p in cleaned.split(">") if p.strip()]
    return [normalize_channel(p) for p in parts]

def classify_criticality(criticality, risk, priority, category):
    criticality = criticality.upper()
    risk = risk.upper()

    if criticality == "HIGH" and risk == "HIGH":
        return "CRITICAL"

    if category.upper() in ["SECURITY", "AUTHENTICATION"]:
        return "CRITICAL" if priority >= 8 else "HIGH"

    if priority >= 9:
        return "CRITICAL"
    if priority >= 7:
        return "HIGH"

    return "NORMAL"

def determine_retries(retry_percentage, classification):
    retry_percentage = float(retry_percentage)

    if retry_percentage >= 55:
        attempts = 3
    elif retry_percentage >= 45:
        attempts = 2
    else:
        attempts = 1

    if classification == "CRITICAL":
        return max(attempts, 3)

    return min(attempts, 2)

def customer_behavior_mode(trend: str):
    trend = trend.strip().upper()

    if "SPAM" in trend:
        return "LIMIT_PUSHING"
    if "IGNORED" in trend:
        return "BOOST_URGENCY"
    if "CLICKED" in trend:
        return "PREFER_DIGITAL"
    if "VIEWED" in trend:
        return "BALANCED"

    return "BALANCED"

def determine_delivery_mode(classification, behavior):
    if classification == "CRITICAL":
        return "PARALLEL"
    return "SEQUENTIAL"

def load_policies():
    policies = {}

    with open(MASTER_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            et = row["Event_Type"].strip().upper()

            category = row["Event_Category"]
            criticality = row["Criticality_Level"]
            risk = row["Risk_Level"]
            priority = int(row["Priority_Score"])

            retry_pct = row["Retry_Percentage"]
            raw_success = row["Delivery_Success_Percentage"].strip().replace("%", "")
            success_pct = float(raw_success) if raw_success else 0.0

            customer_trend = row["Customer_Action_Trend"]

            primary = normalize_channel(row["Recommended_Primary_Channel"])
            fallback = split_channels(row["Recommended_Fallback_Channel(s)"])
            secure = row["Secure_Inbox_Required_YN"].strip().upper() == "YES"

            classification = classify_criticality(criticality, risk, priority, category)
            behavior = customer_behavior_mode(customer_trend)
            delivery_mode = determine_delivery_mode(classification, behavior)

            channels = [primary] + fallback
            retry_attempts = determine_retries(retry_pct, classification)

            channel_configs = []
            for c in channels:
                channel_configs.append({
                    "name": c,
                    "success_rate": success_pct,
                    "max_attempts": retry_attempts,
                    "wait_for": 1 if delivery_mode == "PARALLEL" else 3,
                })

            escalation = []
            if classification == "CRITICAL":
                escalation = ["PHONE_CALL", "SECURE_INBOX", "OPS_ALERT"]
            elif classification == "HIGH" and behavior == "BOOST_URGENCY":
                escalation = ["SECURE_INBOX"]

            policies[et] = {
                "priority": priority,
                "classification": classification,
                "category": category,
                "delivery_mode": delivery_mode,
                "behavior_mode": behavior,
                "channels": channel_configs,
                "retry_attempts": retry_attempts,
                "secure_inbox": secure,
                "escalation": escalation
            }

    return policies

POLICIES = load_policies()

# REQUIRED FOR spam_filter.py
def get_allowed_event_types():
    return list(POLICIES.keys())

def get_policy_for(event_type: str):
    return POLICIES.get(event_type.upper(), {
        "priority": 5,
        "classification": "NORMAL",
        "delivery_mode": "SEQUENTIAL",
        "channels": [],
        "secure_inbox": False,
        "escalation": []
    })
