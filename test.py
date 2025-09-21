from flask import Flask, request, jsonify
import logging, os
from interpreter import Interpreter

llm_config = {
    "model": "gpt-4",
    "api_key": os.getenv("OPENAI_API_KEY", "dummy_key"),
}

logging.getLogger("werkzeug").setLevel(logging.ERROR)
app = Flask(__name__)

@app.post("/stream")
def stream():
    payload = request.get_json(force=True, silent=True) or {}
    token = payload.get("token", "")
    last = payload.get("last", False)

    # Print incoming chunks for debug
    print(token, end="", flush=True)
    
    #print("\n--- end of message ---", flush=True)
    print("I am finished...")
    agent = Interpreter(llm_config=llm_config)
    result = agent.interpret(token)  # token must contain the FULL text
    return jsonify({"ok": True, "result": result})
    
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)