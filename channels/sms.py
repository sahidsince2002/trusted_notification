import time
import random

class SMSProviderMock:
    def __init__(self, reliability=0.95, avg_latency=0.4):
        self.reliability = reliability
        self.avg_latency = avg_latency

    def send(self, to, template, metadata):
        time.sleep(self.avg_latency * (0.5 + random.random()))

        if str(to).endswith("0000"):
            return {"status": "PERMANENT_FAILURE", "code": "INVALID_NUMBER"}

        if random.random() < self.reliability:
            return {"status": "DELIVERED", "message_id": str(random.randint(10000,99999))}

        return {"status": "UNDELIVERED", "code": "TEMP_ERROR"}

sms_provider = SMSProviderMock()
