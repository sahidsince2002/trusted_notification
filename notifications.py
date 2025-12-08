# notifications.py (updated)
import time
import threading
from rules_engine import get_policy_for
from workers import dispatcher
from db import (
    check_idempotency,
    insert_idempotency,
    init_db,
    create_event,
    log_attempt,
    update_event_status,
)
from utils import gen_event_id
from spam_filter import is_spam_notification

init_db()


def execute_channel(event_id, event_type, payload, cfg):
    """
    Execute sends for a single channel configuration.
    cfg contains keys: name, max_attempts, wait_for, success_rate (from rules_engine)
    """
    channel = cfg["name"]
    attempts = int(cfg.get("max_attempts", 1))
    wait_for = cfg.get("wait_for", 1)

    for attempt in range(1, attempts + 1):

        # pass configured success rate to dispatcher
        result = dispatcher.send_to_provider(
            channel,
            payload,
            cfg.get("success_rate")
        )

        # treated delivered if result.status == DELIVERED
        delivered = (result.get("status") == "DELIVERED")

        # Log attempt with provider response + metadata
        log_attempt(
            event_id,
            event_type,
            channel,
            attempt,
            str(result),
            "SUCCESS" if delivered else "FAILURE"
        )

        if delivered:
            return True

        # if PERMANENT_FAILURE, stop trying this channel
        if result.get("status") == "PERMANENT_FAILURE":
            # permanent issue — no point retrying this channel
            break

        time.sleep(wait_for)

    return False


def execute_escalation_chain(event_id, event_type, steps):
    for step in steps:
        time.sleep(1)
        log_attempt(
            event_id, event_type, step, 0,
            f"Escalation executed: {step}", "ESCALATION_TRIGGERED"
        )

    update_event_status(event_id, "ESCALATED")
    return {"event_id": event_id, "status": "ESCALATED"}


def process_event(event_id, event_type, payload, policy):

    update_event_status(event_id, "PROCESSING")
    channels_cfg = policy.get("channels", [])
    mode = policy.get("delivery_mode", "SEQUENTIAL")
    escalation = policy.get("escalation", [])

    # PARALLEL
    if mode == "PARALLEL":
        results = {"delivered": False}
        threads = []

        def fn(cfg):
            try:
                if execute_channel(event_id, event_type, payload, cfg):
                    results["delivered"] = True
            except Exception:
                # protect worker thread from crashing
                pass

        for cfg in channels_cfg:
            t = threading.Thread(target=fn, args=(cfg,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if results["delivered"]:
            update_event_status(event_id, "DELIVERED")
            return

        return execute_escalation_chain(event_id, event_type, escalation)

    # SEQUENTIAL
    else:
        for cfg in channels_cfg:
            if execute_channel(event_id, event_type, payload, cfg):
                update_event_status(event_id, "DELIVERED")
                return

        if escalation:
            return execute_escalation_chain(event_id, event_type, escalation)

        update_event_status(event_id, "FAILED")


def send_event(event_type, payload, idempotency_key=None):
    """
    Entrypoint for sending an event.

    Validation behaviour:
      - We do NOT block if some policy channels are missing contact details.
      - Instead we log/allow the event and let the workers attempt each policy channel.
      - Channels with missing contact details will return PERMANENT_FAILURE immediately
        from the dispatcher and will be logged as attempts.
    """

    # Spam check
    if is_spam_notification(event_type, payload):
        event_id = gen_event_id()
        create_event(event_id, event_type, "SPAM_BLOCKED")

        log_attempt(
            event_id, event_type, "SPAM_FILTER", 0,
            "Blocked by spam filter", "SPAM_BLOCKED"
        )

        return {"status": "SPAM_BLOCKED", "event_id": event_id}

    # idempotency
    if idempotency_key:
        existing = check_idempotency(idempotency_key)
        if existing:
            return {"status": "ALREADY_PROCESSED", "event_id": existing}

    # Basic required field: message must exist
    if not payload.get("message"):
        return {"status": "INVALID_PAYLOAD", "message": "Message cannot be empty"}

    # Create event and record idempotency
    event_id = gen_event_id()
    create_event(event_id, event_type, "RECEIVED")

    if idempotency_key:
        insert_idempotency(idempotency_key, event_id)

    # Policy-aware behaviour: do not block on missing contact fields.
    policy = get_policy_for(event_type)

    # If any channels are missing contact info, optionally log a warning (server-side).
    channels = [c.get("name") for c in policy.get("channels", [])]
    missing = []
    if "SMS" in channels and not payload.get("to"):
        missing.append("SMS")
    if "EMAIL" in channels and not payload.get("email"):
        missing.append("EMAIL")
    if "PUSH" in channels and not payload.get("device_token"):
        missing.append("PUSH")
    if "WHATSAPP" in channels and not payload.get("wa_number"):
        missing.append("WHATSAPP")

    if missing:
        # server-side diagnostics only, does not block sending
        print(f"[notifications] Warning: missing contact info for channels: {', '.join(missing)}")

    # spawn background worker to process event according to policy
    worker = threading.Thread(target=process_event, args=(event_id, event_type, payload, policy))
    worker.start()

    return {"status": "ACCEPTED", "event_id": event_id}
