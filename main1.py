from flask import Flask, request, jsonify
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.post("/stream")
def stream():
    payload = request.get_json(force=True, silent=True) or {}
    token = payload.get("token", "")
    last = payload.get("last", False)

    # Print each chunk as it arrives
    print(token, end="", flush=True)
    if last:
        print("\n--- end of message ---", flush=True)

    return jsonify({"ok": True})

if __name__ == "__main__":
    # Runs on http://localhost:5001/stream
    app.run(host="127.0.0.1", port=5001, debug=False)
