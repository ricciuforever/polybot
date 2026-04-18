#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

# Crea il virtual environment isolato se non esiste
python3 -m venv venv

# Aggiorna pip per evitare i crash di sistema
venv/bin/python -m pip install --upgrade pip

# Installa o aggiorna le librerie
venv/bin/pip install -r requirements.txt

# Chiude processi vecchi se esistono (per evitare conflitti di porta 5000)
pkill -f "web_server_v2.py" || true

# Avvia il server in background e salva i log
nohup venv/bin/python web_server_v2.py > dashboard_log.txt 2>&1 &
