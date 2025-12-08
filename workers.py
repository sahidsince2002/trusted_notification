# workers.py (updated)
import random
import time

# provider mocks - keep these imports in sync with your project structure
from channels.sms import sms_provider
from channels.email import email_provider
from channels.push import push_provider

# optional - if you have whatsapp provider
try:
    from channels.whatsapp import whatsapp_provider
    HAS_WHATSAPP = True
except Exception:
    whatsapp_provider = None
    HAS_WHATSAPP = False


class NotificationDispatcher:
    """
    Single entrypoint for sending to channel providers.

    send_to_provider(channel, payload, configured_rate)
      - configured_rate: float (0-100) baseline from master sheet
      - returns dict:
            {
              "status": "DELIVERED" | "FAILED" | "PERMANENT_FAILURE",
              "provider_response": {... or None...},
              "configured_provider_rate": 48.48,
              "effective_rate": 51.23
            }
    """

    def _apply_variation(self, configured_rate):
        """
        Apply ±5% absolute variation to configured rate.
        Example: configured 48.48 -> random add between -5.0 and +5.0 percentage points.
        Clip between 0 and 100.
        """
        if configured_rate is None:
            configured = 50.0
        else:
            configured = float(configured_rate)

        variation = random.uniform(-5.0, 5.0)
        effective = configured + variation
        if effective < 0:
            effective = 0.0
        if effective > 100:
            effective = 100.0
        return round(configured, 2), round(effective, 2)

    def send_to_provider(self, channel, payload, configured_rate=None):
        """
        Channel-aware send. Does basic validation for missing contact info,
        then simulates delivery using effective probability (configured_rate ±5%).
        """

        channel = (channel or "").upper()

        # Validate contact presence first -> PERMANENT_FAILURE if not present
        if channel == "SMS":
            to = payload.get("to")
            if not to:
                return {
                    "status": "PERMANENT_FAILURE",
                    "provider_response": None,
                    "configured_provider_rate": configured_rate,
                    "effective_rate": None,
                    "reason": "NO_PHONE_PROVIDED"
                }

        if channel == "EMAIL":
            email = payload.get("email")
            if not email:
                return {
                    "status": "PERMANENT_FAILURE",
                    "provider_response": None,
                    "configured_provider_rate": configured_rate,
                    "effective_rate": None,
                    "reason": "NO_EMAIL_PROVIDED"
                }

        if channel == "PUSH":
            token = payload.get("device_token")
            if not token:
                return {
                    "status": "PERMANENT_FAILURE",
                    "provider_response": None,
                    "configured_provider_rate": configured_rate,
                    "effective_rate": None,
                    "reason": "NO_DEVICE_TOKEN"
                }

        if channel == "WHATSAPP":
            if not HAS_WHATSAPP:
                return {
                    "status": "PERMANENT_FAILURE",
                    "provider_response": None,
                    "configured_provider_rate": configured_rate,
                    "effective_rate": None,
                    "reason": "WHATSAPP_NOT_CONFIGURED"
                }
            wa_num = payload.get("wa_number")
            if not wa_num:
                return {
                    "status": "PERMANENT_FAILURE",
                    "provider_response": None,
                    "configured_provider_rate": configured_rate,
                    "effective_rate": None,
                    "reason": "NO_WA_NUMBER"
                }

        # compute effective rate
        configured, effective = self._apply_variation(configured_rate)

        # Call underlying provider (we still capture provider_response for visibility,
        # but we will use `effective` to decide final success for the system to be consistent)
        provider_resp = None
        try:
            if channel == "SMS":
                provider_resp = sms_provider.send(payload.get("to"), payload.get("message"), {})
            elif channel == "EMAIL":
                provider_resp = email_provider.send(payload.get("email"), payload.get("message"), {})
            elif channel == "PUSH":
                provider_resp = push_provider.send(payload.get("device_token"), payload.get("message"), {})
            elif channel == "WHATSAPP":
                provider_resp = whatsapp_provider.send(payload.get("wa_number"), payload.get("message"), {})
            else:
                return {
                    "status": "PERMANENT_FAILURE",
                    "provider_response": None,
                    "configured_provider_rate": configured,
                    "effective_rate": effective,
                    "reason": f"UNKNOWN_CHANNEL:{channel}"
                }
        except Exception as e:
            # provider raised; treat as transient provider failure
            provider_resp = {"status": "UNDELIVERED", "error": str(e)}

        # Decide success using effective probability
        roll = random.random() * 100.0
        delivered_by_prob = roll <= effective

        # Map provider_resp.status normalization
        prov_status = None
        if isinstance(provider_resp, dict):
            prov_status = provider_resp.get("status")
        elif provider_resp is None:
            prov_status = None
        else:
            # fallback: attempt to interpret string return
            prov_status = str(provider_resp)

        # Final status decision:
        # - If provider returned PERMANENT_FAILURE-like status, propagate permanent failure.
        # - Else use our probability roll to mark DELIVERED or FAILED.
        if prov_status and str(prov_status).upper() in ("PERMANENT_FAILURE", "INVALID_NUMBER", "INVALID_EMAIL", "NO_DEVICE"):
            final_status = "PERMANENT_FAILURE"
        else:
            final_status = "DELIVERED" if delivered_by_prob else "FAILED"

        result = {
            "status": final_status,
            "provider_response": provider_resp,
            "configured_provider_rate": configured,
            "effective_rate": effective,
            "roll": round(roll, 2)
        }

        return result


# single dispatcher instance used by notifications.py
dispatcher = NotificationDispatcher()
