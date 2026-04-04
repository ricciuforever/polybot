import os
import json
from flask import Flask, jsonify, render_template
import logging

# Disabilita i log di Flask per non sporcare la console
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Stato globale condiviso con main.py
bot_state = {
    "balance": 100.0, # Saldo simulato iniziale
    "real_balance": 0.0,
    "matic_balance": 0.0,
    "pending_claims": 0.0,
    "assets": {},
    "logs": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify(bot_state)

@app.route('/api/trades')
def trades():
    path = "data/trades.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding='utf-8') as f:
                return jsonify(json.load(f))
        except Exception:
            return jsonify([])
    return jsonify([])

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_server()
