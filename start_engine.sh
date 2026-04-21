#!/bin/bash
# Script di avvio ottimizzato per il bot in produzione (polybot.emanueletolomei.it)
# Questo script avvia il motore di trading e il sistema di riscatto in modo indipendente.

BASE_DIR="/var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it"
cd $BASE_DIR

echo "🛑 Arresto processi esistenti..."
pkill -f "bot_poly.py" || true
pkill -f "auto_redeemer.py" || true
pkill -f "web_server_v2.py" || true

# Configurazione Python (Plesk venv)
PYTHON_BIN="$BASE_DIR/venv/bin/python"

echo "🚀 Avvio Motore di Trading (bot_poly.py)..."
nohup $PYTHON_BIN bot_poly.py >> logs/engine.log 2>&1 &

echo "💰 Avvio Auto-Redeemer (auto_redeemer.py)..."
nohup $PYTHON_BIN auto_redeemer.py >> logs/redeemer.log 2>&1 &

echo "✅ Motore avviato correttamente."
echo "ℹ️  Puoi monitorare l'attività tramite la dashboard PHP o i file di log nella cartella logs/."
