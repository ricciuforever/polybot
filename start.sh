#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

# Cerchiamo la versione aggiornata di Python (Polymarket richiede >= 3.9.10)
# Usiamo il path assoluto perché il cron di Plesk ignora /usr/local/bin
PYTHON_CMD="/usr/local/bin/python3.11"
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3" # Fallback disperato
fi

echo "Utilizzando $PYTHON_CMD per la creazione del venv..."

# Cancella il vecchio venv 3.8 se esiste per forzare un ambiente pulito 3.9
rm -rf venv

# Crea il virtual environment isolato
$PYTHON_CMD -m venv venv

# Aggiorna pip
venv/bin/python -m pip install --upgrade pip

# Installa librerie
venv/bin/pip install -r requirements.txt

# Uccide processi vecchi in memoria
pkill -f "web_server_v2.py" || true

# Avvia server
nohup venv/bin/python web_server_v2.py > dashboard_log.txt 2>&1 &
