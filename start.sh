#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

# CONTROLLO INTELLIGENTE:
# Se il processo è già attivo, esci senza fare nulla.
# Questo permette di impostare il Cron ogni 5 minuti senza interrompere il bot.
if pgrep -f "web_server_v2.py" > /dev/null; then
    echo "Il Bot è già operativo. Watchdog completato."
    exit 0
fi

echo "Bot non rilevato. Avvio procedura di ripristino..."

# Cerchiamo la versione aggiornata di Python (Polymarket richiede >= 3.9.10)
PYTHON_CMD="/usr/local/bin/python3.11"
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3" # Fallback
fi

# Crea il virtual environment isolato se non c'è
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
fi

# Installazione dipendenze
venv/bin/python -m pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo "Avvio del Server Web (Manager) in Foreground..."
# Eseguiamo in primo piano così Plesk mantiene vivo il task
venv/bin/python web_server_v2.py
