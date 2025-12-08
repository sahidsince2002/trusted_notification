import time, random

class WhatsAppProviderMock:
    def __init__(self, reliability=0.88):
        self.reliability = reliability

    def send(self, number, message, metadata):
        time.sleep(0.4)

        if not number:
            return {"status": "PERMANENT_FAILURE", "code": "INVALID_WA_NUMBER"}

        if random.random() < self.reliability:
            return {"status": "DELIVERED"}

        return {"status": "UNDELIVERED", "code": "TEMP_ERROR"}

whatsapp_provider = WhatsAppProviderMock()
