# utils.py
import uuid
import random

def gen_event_id():
    return str(uuid.uuid4())

def backoff_delay(attempt, base=1.0, factor=2.0, max_delay=30.0):
    delay = base * (factor ** (attempt - 1))
    jitter = random.uniform(-delay * 0.1, delay * 0.1)
    return min(max_delay, delay + jitter)
