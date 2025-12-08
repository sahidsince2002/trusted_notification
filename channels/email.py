import time, random

class EmailProviderMock:
    def __init__(self, reliability=0.9):
        self.reliability = reliability

    def send(self, to, message, metadata):
        time.sleep(0.5)

        if not to:
            return {"status": "PERMANENT_FAILURE", "code": "INVALID_EMAIL"}

        if random.random() < self.reliability:
            return {"status": "DELIVERED"}

        return {"status": "UNDELIVERED", "code": "TEMP"}
        
email_provider = EmailProviderMock()
