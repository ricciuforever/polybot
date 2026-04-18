#!/bin/bash
cd /var/www/vhosts/emanueletolomei.it/polybot.emanueletolomei.it

# Se il server sta GIA' girando, esci in modo pulito senza fare nulla (evita doppi spegnimenti)
if pgrep -f "web_server_v2.py" > /dev/null; then
    echo "Il bot sta gia girando. Nessuna azione necessaria."
    exit 0
fi

# Cerchiamo la versione aggiornata di Python (Polymarket richiede >= 3.9.10)
PYTHON_CMD="/usr/local/bin/python3.11"
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3" # Fallback disperato
fi

echo "Avvio preparazione ambiente in Foreground..."

# Crea il virtual environment isolato se non c'è
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
fi

# Installa librerie
venv/bin/python -m pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo "Avvio del Server Web in primo piano (Foreground) per impedire il kill del Cron di Plesk..."
# NON usiamo l'ultimo '&' così Plesk mantiene vivo il processo come un vero demone!
venv/bin/python web_server_v2.py
