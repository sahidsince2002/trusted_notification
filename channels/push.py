import random
import time

class PushProviderMock:
    def __init__(self, reliability=0.85):
        self.reliability = reliability

    def send(self, token, msg, metadata):
        time.sleep(0.4)
        if not token:
            return {"status": "PERMANENT_FAILURE", "code": "NO_DEVICE"}
        if random.random() < self.reliability:
            return {"status": "DELIVERED"}
        return {"status": "UNDELIVERED"}

push_provider = PushProviderMock()
