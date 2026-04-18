#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

# Cerchiamo una versione aggiornata di Python (Polymarket richiede >= 3.9)
PYTHON_CMD=""
for cmd in python3.11 python3.10 python3.9 python3; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done

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
