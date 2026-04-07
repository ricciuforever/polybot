from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder='ui/dist')
CORS(app)

STATE_FILE = "bot_state.json"

@app.route('/api/liquidate', methods=['POST'])
def liquidate():
    try:
        from poly_trader import PolyTrader
        trader = PolyTrader()
        trader.emergency_sell_all()
        return jsonify({"status": "success", "message": "Liquidazione avviata"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    
    with open(STATE_FILE, "r") as f:
        return jsonify(json.load(f))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
