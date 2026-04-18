from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import json
import os
import subprocess
import threading
import time
import sys

app = Flask(__name__, static_folder='ui/dist')
CORS(app)

STATE_FILE = "bot_state.json"
BOT_PROCESS = None
DESIRED_STATE = False

def bot_manager():
    global BOT_PROCESS, DESIRED_STATE
    while True:
        if DESIRED_STATE:
            if BOT_PROCESS is None or BOT_PROCESS.poll() is not None:
                BOT_PROCESS = subprocess.Popen([sys.executable, "bot_poly.py"])
        else:
            if BOT_PROCESS is not None and BOT_PROCESS.poll() is None:
                BOT_PROCESS.terminate()
                BOT_PROCESS.wait()
        time.sleep(2)

threading.Thread(target=bot_manager, daemon=True).start()

@app.route('/api/liquidate', methods=['POST'])
def liquidate():
    try:
        from poly_trader import PolyTrader
        trader = PolyTrader()
        trader.emergency_sell_all()
        return jsonify({"status": "success", "message": "Liquidazione avviata"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    is_running = BOT_PROCESS is not None and BOT_PROCESS.poll() is None
    return jsonify({"desired": DESIRED_STATE, "running": is_running})

@app.route('/api/bot/toggle', methods=['POST'])
def bot_toggle():
    global DESIRED_STATE
    req = request.json or {}
    state = req.get('state')
    if state is not None:
        DESIRED_STATE = bool(state)
    else:
        DESIRED_STATE = not DESIRED_STATE
    return jsonify({"desired": DESIRED_STATE})

@app.route('/api/env', methods=['GET'])
def get_env():
    env_data = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        env_data[k.strip()] = v.strip()
    return jsonify(env_data)

@app.route('/api/env', methods=['POST'])
def set_env():
    from dotenv import set_key
    env_data = request.json or {}
    env_file = ".env"
    if not os.path.exists(env_file):
        open(env_file, 'w', encoding='utf-8').close()
    
    for k, v in env_data.items():
        set_key(env_file, k, str(v))
    
    global BOT_PROCESS
    if BOT_PROCESS is not None and BOT_PROCESS.poll() is None:
        BOT_PROCESS.terminate()
        BOT_PROCESS.wait()
        
    return jsonify({"status": "success", "message": "Ambiente aggiornato. Il bot si riavvierà se era attivo."})

@app.route('/api/state')
def get_state():
    if not os.path.exists(STATE_FILE):
        return jsonify({
            "last_update": 0,
            "live_games": [],
            "ai_logs": [],
            "wallet": {"pol": 0, "usdc": 0, "address": "N/A"},
            "stats": {"total_bets": 0, "won_bets": 0}
        })
    with open(STATE_FILE, "r", encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
