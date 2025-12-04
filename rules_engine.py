# rules_engine.py
import csv

MASTER_CSV = "master_sheet.csv"

def normalize_channel(name: str):
    if not name:
        return None
    name = name.strip().lower()
    if "sms" in name: return "SMS"
    if "push" in name: return "PUSH"
    if "mail" in name or "email" in name: return "EMAIL"
    return name.upper()

def split_channels(raw_value):
    if not raw_value: return []
    cleaned = (raw_value.replace("→", ">")
                         .replace("->", ">")
                         .replace(",", ">")
                         .replace("/", ">"))
    parts = [p.strip() for p in cleaned.split(">") if p.strip()]
    return [normalize_channel(p) for p in parts]

def classify_criticality(criticality, risk, priority):
    criticality = criticality.upper()
    risk = risk.upper()
    priority = int(priority)
    if criticality == "HIGH" and risk == "HIGH":
        return "CRITICAL"
    if priority >= 8:
        return "HIGH"
    return "NORMAL"

def get_allowed_event_types():
    return list(POLICIES.keys())

def load_policies():
    policies = {}
    with open(MASTER_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            et = row["Event_Type"].strip().upper()
            priority = int(row["Priority_Score"])
            primary = normalize_channel(row["Recommended_Primary_Channel"])
            fallback = split_channels(row["Recommended_Fallback_Channel(s)"])
            secure = row["Secure_Inbox_Required_YN"].strip().upper() == "YES"

            classification = classify_criticality(
                row["Criticality_Level"], row["Risk_Level"], priority
            )

            channels = [primary] + fallback

            channel_configs = [{
                "name": c,
                "wait_for": 1 if classification == "CRITICAL" else 5,
                "max_attempts": 3 if classification == "CRITICAL" else 2,
                "permanent_failure_codes": []
            } for c in channels]

            if classification == "CRITICAL":
                policies[et] = {
                    "priority": priority,
                    "classification": "CRITICAL",
                    "immediate": True,
                    "delivery_mode": "PARALLEL",
                    "ack_timeout": 4,
                    "total_timeout": 15,
                    "fanout_providers": ["SMS_PROVIDER_A", "SMS_PROVIDER_B"],
                    "escalation": ["PHONE_CALL", "SECURE_INBOX", "OPS_ALERT"],
                    "channels": channel_configs,
                    "secure_inbox": secure
                }
            else:
                policies[et] = {
                    "priority": priority,
                    "classification": classification,
                    "immediate": False,
                    "delivery_mode": "SEQUENTIAL",
                    "ack_timeout": None,
                    "total_timeout": None,
                    "fanout_providers": [],
                    "escalation": [],
                    "channels": channel_configs,
                    "secure_inbox": secure
                }

    return policies

POLICIES = load_policies()

def get_policy_for(event_type: str):
    return POLICIES.get(event_type.upper(), {
        "priority": 5,
        "classification": "NORMAL",
        "immediate": False,
        "delivery_mode": "SEQUENTIAL",
        "channels": [],
        "secure_inbox": False
    })
