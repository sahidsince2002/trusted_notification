# app.py
from flask import Flask, request, jsonify, render_template
from notifications import send_event
from db import init_db, get_attempt_logs, clear_logs
from rules_engine import POLICIES

app = Flask(__name__, template_folder="templates", static_folder="static")

# Initialize DB on startup
init_db()


# --------------------------------------------------------
# UI ROUTE → Dashboard
# --------------------------------------------------------
@app.route("/")
def ui():
    return render_template("dashboard.html")


# --------------------------------------------------------
# SEND NOTIFICATION
# --------------------------------------------------------
@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.json or {}
    event_type = data.get("event_type")
    payload = data.get("payload", {})
    idempotency_key = data.get("idempotency_key")

    if not event_type:
        return jsonify({"error": "event_type required"}), 400

    result = send_event(event_type, payload, idempotency_key)
    return jsonify(result), 202


# --------------------------------------------------------
# GET POLICIES
# --------------------------------------------------------
@app.route("/api/policies", methods=["GET"])
def api_policies():
    return jsonify(POLICIES)


# --------------------------------------------------------
# FETCH LOGS (attempts table)
# --------------------------------------------------------
@app.route("/api/logs", methods=["GET"])
def api_logs():
    logs = get_attempt_logs(limit=200)
    return jsonify(logs)


# --------------------------------------------------------
# CLEAR ALL LOGS
# --------------------------------------------------------
@app.route("/api/clear_logs", methods=["POST"])
def api_clear_logs():
    clear_logs()
    return jsonify({"status": "success", "message": "Logs cleared"}), 200


# --------------------------------------------------------
# OPTIONAL: AUDIT TRAIL ENDPOINT (if needed later)
# --------------------------------------------------------
@app.route("/api/audit", methods=["GET"])
def api_audit():
    # If you add audit logging, replace this
    return jsonify([])


# --------------------------------------------------------
# OPTIONAL: POLICY MANAGER ENDPOINT
# --------------------------------------------------------
@app.route("/api/update_policy", methods=["POST"])
def api_update_policy():
    data = request.json
    # Future: implement policy editing here
    return jsonify({"message": "Policy update API placeholder"})


# --------------------------------------------------------
# MAIN RUN
# --------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
