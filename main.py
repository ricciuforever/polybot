"""
main.py — Headless Azuro Sniper Bot V3 (Polygon)
"""
import sys
import time
import os
import signal
import threading
import json
from eth_account import Account

import config
from modules.logger         import get_logger
from modules.price_feed     import BinanceFeed
from modules.azuro_watcher  import AzuroWatcher
from modules.strategy       import evaluate, HOLD, BUY_UP, BUY_DOWN
from azuro_trader           import AzuroTrader
from web_server             import run_server, bot_state

log = get_logger("main")

TRADES_FILE = "data/trades.json"

_running = True

def _handle_sigint(sig, frame):
    global _running
    log.warning("🛑 Interruzione ricevuta (CTRL+C). Chiusura...")
    _running = False
    os._exit(0)

signal.signal(signal.SIGINT, _handle_sigint)

def kill_port_5000():
    """Rasa tutti i processi appesi sulla porta 5000 (Windows)"""
    try:
        import subprocess
        # Trova i PID sulla porta 5000
        cmd = 'netstat -ano | findstr :5000 | findstr LISTENING'
        output = subprocess.check_output(cmd, shell=True).decode()
        for line in output.strip().split('\n'):
            parts = line.split()
            if len(parts) > 4:
                pid = parts[-1]
                log.warning(f"Raso processo appeso sulla porta 5000 (PID: {pid})...")
                subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
    except Exception:
        pass

def main():
    global _running
    
    kill_port_5000()
    
    log.info("=" * 60)
    log.info(" Azuro Headless Sniper Bot V3  —  Polygon Network")
    log.info("=" * 60)
    log.info(f"Modalità: {'DRY-RUN' if config.DRY_RUN else '*** LIVE ***'}")
    log.info(f"Min Odds: {config.MIN_ODDS} | Bet: {config.BET_SIZE} USDC.e")
    log.info(f"Loop Interval: {config.LOOP_INTERVAL}s")

    # 1. VALIDAZIONE CONFIG
    try:
        config.validate()
    except EnvironmentError as e:
        log.critical(str(e))
        sys.exit(1)

    # 2. INIZIALIZZAZIONE COMPONENTI
    feed = BinanceFeed()
    feed.start()
    
    watcher = AzuroWatcher()
    trader = AzuroTrader()
    
    # Check connessione Wallet/RPC
    ok, msg = trader.check_connection()
    if not ok:
        log.error(f"Errore connessione: {msg}")
        if not config.DRY_RUN: sys.exit(1)

    # 3. STATO INIZIALE & SALDI
    pol_bal, usdc_bal = trader.get_balances()
    bot_state["real_balance"] = usdc_bal
    bot_state["matic_balance"] = pol_bal
    bot_state["pnl"] = 0.0 # PnL Iniziale (dal riavvio)

    # 3. DASHBOARD WEB (Opzionale, mantenuta per monitoraggio)
    log.info("Avvio dashboard web su http://localhost:5000")
    threading.Thread(target=run_server, daemon=True).start()

    log.info("Attendo warm-up feed Binance...")
    time.sleep(3)

    log.info("-" * 60)
    log.info(f"Sniper Operativo (USDC). Ricerca mercati per: {', '.join(config.ASSETS)}")

    while _running:
        try:
            # Aggiornamento saldi per UI ad ogni ciclo
            pol_bal, usdc_bal = trader.get_balances()
            bot_state["real_balance"] = usdc_bal
            bot_state["matic_balance"] = pol_bal
            
            now_ts = int(time.time())
            
            # --- CICLO ASSET ---
            for asset in config.ASSETS:
                # --- PREZZI BINANCE & OSCILLAZIONE ---
                price = feed.get_last_price(asset)
                movement = feed.get_window_movement(asset)
                trend = feed.get_trend_direction(asset)
                threshold = config.THRESHOLDS.get(asset, 0.03)

                # --- RICERCA MERCATO ---
                market = watcher.find_market(asset)
                
                if not market:
                    log.debug(f"[{asset}] Mov: {movement:+.3f}% (S: {threshold}%) | Nessun mercato found.")
                    continue

                condition_id = market['conditionId']
                title = market['title']
                outcomes = market['outcomes']
                starts_at = market['startsAt']
                time_left = max(0, starts_at - now_ts)
                
                up_odds = outcomes.get('1', 1.0)
                down_odds = outcomes.get('2', 1.0)
                
                # Log nello stile Legacy (Oscillazione)
                # log.debug(f"[{asset}] Mov: {movement:+.4f}% | Sogl: {threshold}% | P: ${price:.2f} | T: {time_left}s")

                # Aggiornamento stato per la Dashboard Bento per ogni asset
                bot_state["assets"][asset] = {
                    "price": price,
                    "movement": movement,
                    "threshold": threshold,
                    "up_odds": up_odds,
                    "down_odds": down_odds,
                    "market_title": title,
                    "time_left": time_left,
                    "trend": trend,
                    "updated": time.strftime("%H:%M:%S")
                }
                bot_state["dry_run"] = config.DRY_RUN

                # --- STRATEGIA ---
                action, confidence = evaluate(asset, movement, up_odds, down_odds, time_left, trend, threshold)

                if action != HOLD:
                    outcome_id = 1 if action == BUY_UP else 2
                    odds = up_odds if action == BUY_UP else down_odds
                    
                    msg = f"🎯 SEGNALE [{asset}]: {action} @ {odds:.2f} su {title}"
                    log.info(msg)
                    bot_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
                    if len(bot_state["logs"]) > 20: bot_state["logs"].pop(0)
                    
                    if config.DRY_RUN:
                        log.info(f"🧪 [DRY-RUN] Simulata bet da 1.0 USDC su {asset}")
                        bot_state["balance"] -= config.BET_SIZE
                    else:
                        success, tx_hash = trader.execute_bet(condition_id, outcome_id, config.BET_SIZE, config.MIN_ODDS, core_address=market.get("core"))
                        if success:
                            log.info(f"💰 BET {asset} CONFERMATA! TX: {tx_hash}")
                            bot_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] 💰 BET {asset} CONFERMATA!")
                        else:
                            log.error(f"❌ Fallimento Bet {asset}: {tx_hash}")

                    time.sleep(2)

                    # --- SALVATAGGIO TRADE ---
                    new_trade = {
                        "asset": asset,
                        "action": action,
                        "amount": config.BET_SIZE,
                        "odds": odds,
                        "title": title,
                        "timestamp": int(time.time()),
                        "status": "dry-run" if config.DRY_RUN else "pending"
                    }
                    
                    # Update local trades file
                    trades = []
                    if os.path.exists(TRADES_FILE):
                        try:
                            with open(TRADES_FILE, "r") as f:
                                trades = json.load(f)
                        except: pass
                    
                    trades.append(new_trade)
                    os.makedirs("data", exist_ok=True)
                    with open(TRADES_FILE, "w") as f:
                        json.dump(trades, f, indent=4)

            # AGGIORNAMENTO SALDI PERIODICO (ogni ciclo o n cicli)
            if config.DRY_RUN:
                # In dry-run il balance simulato scende, il reale resta fisso
                pass
            else:
                p_bal, u_bal = trader.get_balances()
                bot_state["real_balance"] = u_bal
                bot_state["matic_balance"] = p_bal

            time.sleep(config.LOOP_INTERVAL)

        except Exception as e:
            log.exception(f"ERRORE nel loop principale: {e}")
            time.sleep(10)

    log.info("Bot fermato.")

if __name__ == "__main__":
    main()
