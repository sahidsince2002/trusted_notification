# db.py
import sqlite3
import threading

DB_FILE = "notifications.db"
_lock = threading.Lock()

def init_db():
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        # EVENTS TABLE
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ATTEMPTS TABLE (FIXED: event_type added)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            event_type TEXT,
            channel TEXT,
            attempt_no INTEGER,
            provider_response TEXT,
            status TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # IDEMPOTENCY
        cur.execute("""
        CREATE TABLE IF NOT EXISTS idempotency (
            key TEXT PRIMARY KEY,
            event_id TEXT
        )
        """)

        conn.commit()
        conn.close()


def update_event_status(event_id, status):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("UPDATE events SET status=? WHERE event_id=?", (status, event_id))
        conn.commit()
        conn.close()


def save_secure_message(event_id, payload):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS secure_inbox (
            event_id TEXT PRIMARY KEY,
            payload TEXT,
            stored_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("INSERT OR REPLACE INTO secure_inbox(event_id, payload) VALUES (?, ?)",
                    (event_id, str(payload)))
        conn.commit()
        conn.close()


# FIX: event_type added
def log_attempt(event_id, event_type, channel, attempt_no, response, status):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO attempts(event_id, event_type, channel, attempt_no, provider_response, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, event_type, channel, attempt_no, response, status))
        conn.commit()
        conn.close()


def get_attempt_logs(limit=100):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        cur.execute("""
        SELECT event_id, event_type, channel, attempt_no, provider_response, status, ts
        FROM attempts
        ORDER BY ts DESC LIMIT ?
        """, (limit,))

        rows = cur.fetchall()
        conn.close()

        return [{
            "event_id": r[0],
            "event_type": r[1],
            "channel": r[2],
            "attempt_no": r[3],
            "response": r[4],
            "status": r[5],
            "timestamp": r[6]
        } for r in rows]


def check_idempotency(key):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT event_id FROM idempotency WHERE key=?", (key,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None


def insert_idempotency(key, event_id):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO idempotency(key, event_id) VALUES (?, ?)",
                    (key, event_id))
        conn.commit()
        conn.close()


def clear_logs():
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("DELETE FROM attempts")
        cur.execute("DELETE FROM events")
        conn.commit()
        conn.close()
