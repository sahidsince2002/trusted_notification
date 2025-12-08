import time, random

class SMSProviderMock:
    def __init__(self, reliability=0.95, avg_latency=0.4):
        self.reliability = reliability
        self.avg_latency = avg_latency

    def send(self, to, message, metadata):
        time.sleep(self.avg_latency * (0.5 + random.random()))

        if not to or str(to).endswith("0000"):
            return {"status": "PERMANENT_FAILURE", "code": "INVALID_NUMBER"}

        if random.random() < self.reliability:
            return {"status": "DELIVERED"}

        return {"status": "UNDELIVERED", "code": "TEMP_ERROR"}

sms_provider = SMSProviderMock()
