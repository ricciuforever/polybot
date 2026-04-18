#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

echo "Sincronizzazione e riavvio forzato in corso..."

# Uccidiamo i vecchi processi per ricaricare il codice e le chiavi .env
pkill -f "web_server_v2.py" || true
pkill -f "bot_poly.py" || true

# Cerchiamo la versione aggiornata di Python (Polymarket richiede >= 3.9.10)
PYTHON_CMD="/usr/local/bin/python3.11"
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3" # Fallback
fi

# Crea il virtual environment isolato se non c'è
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
fi

# Aggiorna pip e installa librerie (incluso web3 ora presente)
venv/bin/python -m pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo "Avvio del Server Web (Manager) in Foreground..."
# Eseguiamo in primo piano così Plesk mantiene vivo il task
venv/bin/python web_server_v2.py
