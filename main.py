"""
main.py — Entry point di PolyBot v1.0 (Multi-Asset)
"""
import sys
import time
import os
import json
import threading
import signal
import requests
import socket
from eth_account import Account

import config
from modules.logger         import get_logger
from modules.geocheck       import check as geocheck
from modules.price_feed     import BinanceFeed
from modules.market_watcher import MarketWatcher
from modules.strategy       import evaluate, HOLD
from modules.trader         import execute, get_wallet_balance
from modules.redeem         import check_winnings, get_matic_balance, auto_redeem, load_trades_robust, sync_external_winnings
from web_server             import run_server, bot_state

log = get_logger("main")

def save_trade(market_data, action, asset):
    """Salva la scommessa nel file trades.json per il redeem futuro."""
    try:
        os.makedirs("data", exist_ok=True)
        path = "data/trades.json"
        
        trades = load_trades_robust()
        
        trades.append({
            "asset": asset,
            "slug": market_data["slug"],
            "conditionId": market_data["conditionId"],
            "action": action,
            "timestamp": time.time(),
            "status": "pending"
        })
        
        with open(path, "w", encoding='utf-8') as f:
            json.dump(trades, f, indent=4)
        log.info(f"💾 Scommessa salvata nello storico: {market_data['slug']} ({action})")
    except Exception as e:
        log.error(f"Errore salvataggio storico trades: {e}")

_running = True
_lock_socket = None

def _handle_sigint(sig, frame):
    global _running
    log.warning("🛑 Interruzione ricevuta (CTRL+C). Chiusura forzata...")
    _running = False
    # Forza l'uscita immediata per evitare thread appesi
    os._exit(0)

signal.signal(signal.SIGINT, _handle_sigint)

def check_single_instance():
    """Impedisce l'avvio di più istanze del bot usando un socket lock."""
    global _lock_socket
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Usiamo una porta arbitraria per il lock (diversa da quella del server web)
        _lock_socket.bind(('127.0.0.1', 49999))
    except socket.error:
        print("\n❌ ERRORE: Il bot è già in esecuzione in un'altra finestra!")
        print("Chiudi la vecchia istanza prima di avviarne una nuova.\n")
        sys.exit(1)

def get_target_price(asset: str, bucket_ts: int) -> float | None:
    """Recupera il prezzo di apertura (Price to Beat) dal minuto di inizio finestra su Binance."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": f"{asset}USDT", "interval": "1m", "startTime": bucket_ts * 1000, "limit": 1}
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if data and len(data) > 0:
            return float(data[0][1])  # Open price
    except Exception as e:
        log.debug(f"get_target_price error per {asset}: {e}")
    return None

def main():
    # Controllo istanza singola
    check_single_instance()
    
    log.info("=" * 60)
    log.info(" PolyBot v1.0  —  Prediction Market Algorithmic Trader")
    log.info("=" * 60)
    log.info(f"Modalità: {'DRY-RUN (simulazione)' if config.DRY_RUN else '*** LIVE TRADING ***'}")
    log.info(f"Asset supportati: {', '.join(config.ASSETS)}")
    log.info(f"Soglie: {config.THRESHOLDS}")
    log.info(f"Bet: {config.BET_SIZE} USDC")

    # 1. VALIDAZIONE CONFIG
    try:
        config.validate()
    except EnvironmentError as e:
        log.critical(str(e))
        sys.exit(1)

    # 2. GEOCHECK
    log.info("Controllo geolocalizzazione IP...")
    try:
        geocheck()
    except RuntimeError as e:
        log.critical(str(e))
        sys.exit(1)

    # 3. BINANCE FEED (Multi-Asset)
    feed = BinanceFeed()
    feed.start()
    log.info("Attendo 3s per il warm-up del feed Binance...")
    time.sleep(3)

    # 4. DASHBOARD WEB
    log.info("Avvio dashboard web su http://localhost:5000")
    threading.Thread(target=run_server, daemon=True).start()

    # 5. STATO MULTI-ASSET
    watcher = MarketWatcher()
    markets = {asset: None for asset in config.ASSETS}
    target_prices = {asset: 0.0 for asset in config.ASSETS}
    
    market_refresh_counter = 0
    MARKET_REFRESH_INTERVAL = 1
    
    pending_trades = []
    heartbeat_counter = 0

    # Inizializza l'oggetto assets nel bot_state per la UI
    bot_state["assets"] = {}

    log.info(f"Loop avviato — intervallo={config.LOOP_INTERVAL}s | max_bet={config.BET_SIZE} USDC")
    log.info("-" * 60)

    # --- BACKGROUND THREAD PER VINCITE E SALDI ---
    def background_tasks():
        while _running:
            try:
                # 1. Saldo reale
                new_real_balance = get_wallet_balance()
                if new_real_balance is not None:
                    bot_state["real_balance"] = new_real_balance
                
                # 2. MATIC Gas
                new_matic_balance = get_matic_balance(Account.from_key(config.PRIVATE_KEY).address)
                if new_matic_balance is not None:
                    bot_state["matic_balance"] = new_matic_balance
                
                # 3. Controllo vincite e Auto-Redeem (DISATTIVATO PER EVITARE BAN)
                # bot_state["pending_claims"] = check_winnings(config.POLY_PROXY_ADDRESS)
                # if bot_state["pending_claims"] > 0:
                #     auto_redeem()
                
                # 4. Sync esterno (ogni tanto) (DISATTIVATO)
                # sync_external_winnings()
                
            except Exception as e:
                log.error(f"Errore nel thread di background: {e}")
            
            # Aspetta 60 secondi tra un controllo e l'altro
            time.sleep(60)

    threading.Thread(target=background_tasks, daemon=True).start()

    while _running:
        if not _running: break
        try:
            now_ts = int(time.time())
            heartbeat_counter += 1

            if heartbeat_counter % 12 == 0:
                log.info("❤️  Heartbeat: Bot operativo.")

            # --- SETTLEMENT TRADE SIMULATI ---
            for trade in pending_trades[:]:
                if now_ts >= trade["end_time"]:
                    asset = trade.get("asset", "BTC")
                    final_price = feed.get_last_price(asset)
                    win = (trade["action"] == "BUY_UP" and final_price >= trade["target"]) or \
                          (trade["action"] == "BUY_DOWN" and final_price < trade["target"])
                    if win:
                        payout = round(trade["size"] / trade["odds"], 2)
                        bot_state["balance"] += payout
                        log.info(f"🏆 [SIM] VINTA su {asset}! +{payout} USDC | Balance: {bot_state['balance']:.2f}")
                    else:
                        log.info(f"💀 [SIM] PERSA su {asset}. Balance: {bot_state['balance']:.2f}")
                    pending_trades.remove(trade)

            # --- REFRESH MERCATI ---
            if market_refresh_counter >= MARKET_REFRESH_INTERVAL:
                for asset in config.ASSETS:
                    new_market = watcher.find_market(asset)
                    if new_market:
                        if not markets[asset] or new_market.get("slug") != markets[asset].get("slug"):
                            markets[asset] = new_market
                            bucket_ts = new_market.get("bucket", 0)
                            target_prices[asset] = get_target_price(asset, bucket_ts) or feed.get_last_price(asset)
                            log.info(f"Nuovo mercato rilevato [{asset}]: {new_market.get('title')}. Target: ${target_prices[asset]:,.4f}")
                market_refresh_counter = 0

            # Se non c'è nessun mercato attivo, aspetta
            if not any(markets.values()):
                log.warning("Nessun mercato trovato per nessun asset. Riprovo...")
                time.sleep(config.LOOP_INTERVAL)
                market_refresh_counter += 1
                continue

            market_refresh_counter += 1

            # --- VALUTAZIONE MULTI-ASSET ---
            for asset in config.ASSETS:
                if not _running: break
                market = markets[asset]
                if not market:
                    continue

                price = feed.get_last_price(asset)
                movement = feed.get_window_movement(asset)
                trend = feed.get_trend_direction(asset)
                up_price, down_price = watcher.get_prices(market)
                time_left = (market.get("bucket", now_ts) + 300) - now_ts

                # Aggiorna stato per UI
                if asset == "BTC":
                    bot_state.update({
                        "btc_price": price,
                        "movement": movement,
                        "up_price": up_price or 0.5,
                        "down_price": down_price or 0.5,
                        "target_price": target_prices[asset],
                        "oracle_price": price,
                        "market_title": market.get("title", "Unknown"),
                        "dry_run": config.DRY_RUN,
                    })
                
                bot_state["assets"][asset] = {
                    "price": price,
                    "movement": movement,
                    "up_price": up_price or 0.5,
                    "down_price": down_price or 0.5,
                    "target_price": target_prices[asset],
                    "time_left": time_left
                }

                # --- STRATEGIA ---
                threshold = config.THRESHOLDS.get(asset, 0.06)
                action, confidence = evaluate(asset, movement, up_price, down_price, time_left, trend, threshold)

                if action != HOLD:
                    token_up, token_down = watcher.get_token_ids(market)
                    success = execute(action, token_up, token_down, up_price, down_price, confidence)
                    if success:
                        if not config.DRY_RUN:
                            save_trade(market, action, asset)
                        if config.DRY_RUN:
                            odds = (up_price if action == "BUY_UP" else down_price) or 0.5
                            end_time = market.get("bucket", now_ts) + 300
                            pending_trades.append({
                                "asset": asset,
                                "market": market.get("slug"),
                                "action": action,
                                "price": odds,
                                "expiry": end_time,
                                "target": target_prices[asset],
                                "size": config.BET_SIZE,
                                "odds": odds,
                                "end_time": end_time
                            })
                            bot_state["balance"] -= config.BET_SIZE
                            log.info(f"🚀 [SIM] Scommessa {action} su {asset} @ {odds:.2f} | Balance: {bot_state['balance']:.2f}")

            time.sleep(config.LOOP_INTERVAL)

        except Exception as e:
            log.exception(f"ERRORE CRITICO nel loop: {e}")
            time.sleep(10)

    feed.stop()
    log.info("PolyBot arrestato.")

if __name__ == "__main__":
    main()
