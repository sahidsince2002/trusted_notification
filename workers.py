# workers.py
import time
import concurrent.futures
from db import log_attempt, update_event_status, save_secure_message
from channels.sms import sms_provider
from channels.email import email_provider
from channels.push import push_provider
from utils import backoff_delay


class NotificationDispatcher:
    def __init__(self, max_workers=20):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_event(self, event_id, event_type, payload, policy):
        self.executor.submit(self._process_event, event_id, event_type, payload, policy)

    def _process_event(self, event_id, event_type, payload, policy):
        if policy["classification"] == "CRITICAL" and policy["delivery_mode"] == "PARALLEL":
            return self._send_critical_parallel(event_id, event_type, payload, policy)
        return self._send_sequential(event_id, event_type, payload, policy)

    # --------------------------------------------------------------------
    # CRITICAL PARALLEL
    # --------------------------------------------------------------------
    def _send_critical_parallel(self, event_id, event_type, payload, policy):

        sms_providers = policy["fanout_providers"]
        futures = [
            self.executor.submit(lambda: self._send_sms(event_id, event_type, payload, p))
            for p in sms_providers
        ]

        start = time.time()
        total_timeout = policy["total_timeout"]

        while time.time() - start < total_timeout:
            for fut in futures:
                if fut.done():
                    resp = fut.result()

                    log_attempt(
                        event_id, event_type, resp["channel"], 1, str(resp), resp["status"]
                    )

                    if resp["status"] == "DELIVERED":
                        update_event_status(event_id, "DELIVERED")
                        return resp

            time.sleep(0.05)

        return {"status": "FAILED", "reason": "Parallel timeout"}

    # --------------------------------------------------------------------
    # SEQUENTIAL DELIVERY
    # --------------------------------------------------------------------
    def _send_sequential(self, event_id, event_type, payload, policy):

        for ch in policy["channels"]:
            channel_name = ch["name"]

            for attempt in range(1, ch["max_attempts"] + 1):

                resp = self._send_channel(event_id, event_type, channel_name, payload)

                log_attempt(
                    event_id,
                    event_type,
                    channel_name,
                    attempt,
                    str(resp),
                    resp["status"]
                )

                if resp["status"] == "DELIVERED":
                    update_event_status(event_id, "DELIVERED")
                    return resp

                if resp["status"] == "PERMANENT_FAILURE":
                    break

                time.sleep(backoff_delay(attempt))

        # secure inbox fallback
        if policy.get("secure_inbox"):
            save_secure_message(event_id, payload)
            update_event_status(event_id, "DELIVERED_SECURE")
            return {"status": "DELIVERED_SECURE"}

        update_event_status(event_id, "FAILED")
        return {"status": "FAILED"}

    # --------------------------------------------------------------------
    # CHANNEL ROUTES
    # --------------------------------------------------------------------
    def _send_channel(self, event_id, event_type, channel, payload):
        if channel == "SMS":
            return self._send_sms(event_id, event_type, payload)
        if channel == "EMAIL":
            return self._send_email(event_id, event_type, payload)
        if channel == "PUSH":
            return self._send_push(event_id, event_type, payload)
        return {"status": "PERMANENT_FAILURE", "reason": "Invalid channel"}

    def _send_sms(self, event_id, event_type, payload, provider_name="SMS"):
        resp = sms_provider.send(payload.get("to"), payload.get("message"), {})
        resp["channel"] = provider_name
        return resp

    def _send_email(self, event_id, event_type, payload):
        resp = email_provider.send(payload.get("email"), payload.get("message"), {})
        resp["channel"] = "EMAIL"
        return resp

    def _send_push(self, event_id, event_type, payload):
        resp = push_provider.send(payload.get("device_token"), payload.get("message"), {})
        resp["channel"] = "PUSH"
        return resp


# global dispatcher
dispatcher = NotificationDispatcher()
