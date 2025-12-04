# notifications.py
from rules_engine import get_policy_for
from workers import dispatcher
from db import check_idempotency, insert_idempotency, init_db
from utils import gen_event_id
from spam_filter import is_spam_notification

init_db()

def send_event(event_type, payload, idempotency_key=None):

    # SPAM CHECK FIX — flagged spam does NOT generate attempts or failures
    if is_spam_notification(event_type, payload):

    # generate an event_id even for spam
        event_id = gen_event_id()

    # insert into events table
        from db import log_attempt, update_event_status
        update_event_status(event_id, "SPAM_BLOCKED")

    # log a synthetic attempt so analytics can count it
        log_attempt(
            event_id=event_id,
            event_type=event_type,
            channel="SPAM_FILTER",
            attempt_no=0,
            response="Blocked by spam filter",
            status="SPAM_BLOCKED"
        )

        return {
           "status": "SPAM_BLOCKED",
           "event_id": event_id,
           "reason": "Notification flagged as suspicious"
        }


    # IDEMPOTENCY
    if idempotency_key:
        existing = check_idempotency(idempotency_key)
        if existing:
            return {"status": "ALREADY_PROCESSED", "event_id": existing}

    event_id = gen_event_id()

    # Register idempotency
    if idempotency_key:
        insert_idempotency(idempotency_key, event_id)

    policy = get_policy_for(event_type)
    dispatcher.submit_event(event_id, event_type, payload, policy)

    return {"status": "ACCEPTED", "event_id": event_id}
