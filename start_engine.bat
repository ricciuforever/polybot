@echo off
echo 🛑 Arresto processi esistenti...
taskkill /F /IM python.exe /T >nul 2>&1

echo 🚀 Avvio Motore di Trading (bot_poly.py)...
start /B python bot_poly.py > logs/engine_win.log 2>&1

echo 💰 Avvio Auto-Redeemer (auto_redeemer.py)...
start /B python auto_redeemer.py > logs/redeemer_win.log 2>&1

echo ✅ Bot avviati in background!
echo 📊 Visualizza logs/engine_win.log per i dettagli.
pause
