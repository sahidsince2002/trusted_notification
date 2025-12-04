# spam_filter.py (replace function)
import re
from rules_engine import get_allowed_event_types

SPAM_KEYWORDS = [
    "congratulations", "you won", "click here", "free", "reward",
    "lottery", "claim now", "visit link"
]

INVALID_COUNTRY_CODES = ("+44", "+234", "+63")

def _normalize_event_name(name):
    if not name:
        return ""
    # remove non-alphanumeric, replace with single space, uppercase and strip
    s = re.sub(r'[^0-9A-Za-z]+', ' ', name).strip().upper()
    # collapse multiple spaces
    s = re.sub(r'\s+', ' ', s)
    return s

def is_spam_notification(event_type, payload):
    message = (payload.get("message") or "").lower()
    phone = str(payload.get("to") or "")

    # 1. Event Type Validation (normalize both sides)
    ALLOWED_EVENTS = get_allowed_event_types()
    # build normalized set once
    normalized_allowed = { _normalize_event_name(e) for e in ALLOWED_EVENTS }

    incoming_norm = _normalize_event_name(event_type)

    # Debug log (optional, safe to keep)
    # print("DEBUG: incoming_norm:", incoming_norm, "allowed:", list(normalized_allowed)[:10])

    if incoming_norm not in normalized_allowed:
        # event unknown -> flag as spam (original behavior)
        return True

    # 2. Keyword Scan
    for word in SPAM_KEYWORDS:
        if word in message:
            return True

    # 3. Suspicious phone numbers
    if phone.startswith(INVALID_COUNTRY_CODES):
        return True

    return False
