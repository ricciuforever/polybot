#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

echo "Riavviando il Bot per applicare aggiornamenti..."

# Uccidiamo i vecchi processi e liberiamo la porta 5050
fuser -k 5050/tcp || true
pkill -f "web_server_v2.py" || true
pkill -f "bot_poly.py" || true
pkill -f "auto_redeemer.py" || true

# Cerchiamo la versione aggiornata di Python (Polymarket richiede >= 3.9.10)
PYTHON_CMD="/usr/local/bin/python3.11"
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3" # Fallback
fi

# Crea il virtual environment isolato se non c'è
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
fi

venv/bin/pip install -r requirements.txt

echo "Avvio Auto-Redeemer in Background..."
nohup venv/bin/python auto_redeemer.py >> auto_redeemer.log 2>&1 &

echo "Avvio del Server Web (Manager) in Background..."
nohup venv/bin/python web_server_v2.py >> web_server.log 2>&1 &

echo "Bot e Server avviati correttamente in background."

# Rotazione manuale semplice dei log bash per evitare che superino ~1MB
for logfile in auto_redeemer.log web_server.log; do
    if [ -f "$logfile" ]; then
        filesize=$(stat -c%s "$logfile")
        if [ "$filesize" -gt 1048576 ]; then
            tail -c 50000 "$logfile" > "${logfile}.tmp"
            mv "${logfile}.tmp" "$logfile"
        fi
    fi
done
