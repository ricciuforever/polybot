import asyncio
import time
import json
import os
import requests
from modules.poly_watcher import PolyWatcher
from modules.price_feed import BinanceFeed
from poly_trader import PolyTrader
import config
from modules.logger import get_logger

log = get_logger("bot_poly")

TRADES_LOG = "trades_history.json"

def load_trades_log():
    if os.path.exists(TRADES_LOG):
        with open(TRADES_LOG) as f:
            return json.load(f)
    return []

def save_trade(entry):
    trades = load_trades_log()
    trades.append(entry)
    with open(TRADES_LOG, "w") as f:
        json.dump(trades, f, indent=2)

def fetch_official_ptb(slug):
    """Tenta di recuperare il Price to Beat ufficiale dall'API di Polymarket."""
    if not slug: return None
    try:
        url = f"https://polymarket.com/api/equity/price-to-beat/{slug}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, (int, float)): return float(data)
            if isinstance(data, dict):
                return float(data.get('price') or data.get('priceToBeat') or 0)
    except Exception as e:
        log.warning(f"Impossibile recuperare PTB ufficiale per {slug}: {e}")
    return None

def update_trade_results():
    """Controlla gli esiti dei trade passati e aggiorna il log."""
    trades = load_trades_log()
    if not trades: return
    
    updated = False
    for t in trades:
        if t.get("result") is not None: continue
        
        # Se il mercato è finito da almeno 2 minuti, controlliamo
        if time.time() > t["market_end"] + 120:
            try:
                cid = t.get("condition_id")
                if not cid: continue
                
                resp = requests.get(f"https://gamma-api.polymarket.com/markets?conditionId={cid}", timeout=5)
                if resp.status_code == 200 and resp.json():
                    m = resp.json()[0]
                    if m.get("closed"):
                        prices = m.get("outcomePrices")
                        if prices:
                            win_index = 0 if float(prices[0]) > 0.5 else 1
                            actual_side = "UP" if win_index == 0 else "DOWN"
                            
                            t["result"] = "WIN" if t["side"] == actual_side else "LOSS"
                            t["payout"] = 1.0 if t["result"] == "WIN" else 0.0
                            updated = True
                            log.info(f"📊 Risultato Trade: {t['market']} -> {t['result']} ({actual_side})")
            except Exception as e:
                log.warning(f"Errore controllo esito per {t['market']}: {e}")
    
    if updated:
        with open(TRADES_LOG, "w") as f:
            json.dump(trades, f, indent=2)
    return updated

class NitroBotPoly:
    def __init__(self):
        self.watcher = PolyWatcher()
        self.feed = BinanceFeed()
        self.trader = PolyTrader()
        self.last_trade_times = {}
        self.running = True
        self.bet_size = config.BET_SIZE
        self.state_file = "bot_state.json"
        
        # Stato per ogni asset monitorato
        self.active_rounds = {asset: {"id": None, "anchor": None, "placed": False} for asset in config.ASSETS}
        
        self.state = {
            "last_update": 0, "live_games": [], "ai_logs": [],
            "wallet": {"pol": 0, "usdc": 0, "address": self.trader.my_address},
            "stats": {"total_bets": 0, "won_bets": 0},
            "recent_trades": []
        }

    async def run(self):
        log.info("🚀 NitroBot POLYMARKET (Smart Sniper v2.1 Multi-Asset) Avviato!")
        log.info(f"Asset: {', '.join(config.ASSETS)}")
        log.info(f"Wallet: {self.trader.my_address}")

        self.feed.start()
        log.info("Attendo warm-up feed Binance...")
        await asyncio.sleep(5)

        cached_markets = []
        last_api_call = 0
        API_REFRESH_INTERVAL = 15
        last_redeem_check = 0
        last_results_check = 0
        
        # PARAMETRI STRATEGIA
        BET_AFTER_SEC = 150
        NO_BET_LAST_SEC = 30
        REDEEM_INTERVAL = 30
        RESULTS_INTERVAL = 300
        MAX_ENTRY_PRICE = 0.65

        while self.running:
            try:
                now = time.time()

                # 1. Refresh mercati (15s)
                if now - last_api_call > API_REFRESH_INTERVAL:
                    cached_markets = self.watcher.find_crypto_markets(limit=50)
                    last_api_call = now

                # 1b. Auto-redeem + saldo (30s)
                if now - last_redeem_check > REDEEM_INTERVAL:
                    self.trader.auto_redeem()
                    pol, usdc = self.trader.get_balances()
                    self.state["wallet"] = {"pol": float(pol), "usdc": float(usdc), "address": self.trader.my_address}
                    last_redeem_check = now

                # 1c. Update esiti (300s)
                if now - last_results_check > RESULTS_INTERVAL:
                    if update_trade_results():
                        trades = load_trades_log()
                        comp = [t for t in trades if t.get("result") is not None]
                        wins = sum(1 for t in comp if t["result"] == "WIN")
                        self.state["stats"] = {"total_bets": len(comp), "won_bets": wins}
                        self.state["recent_trades"] = sorted(trades, key=lambda x: x.get('ts', 0), reverse=True)[:10]
                    last_results_check = now

                # 2. Monitoraggio parallelo dei mercati
                live_games_data = []
                
                for m in cached_markets:
                    asset = m['asset']
                    market_start = m['start_timestamp']
                    market_end = m['end_timestamp']
                    elapsed = now - market_start
                    remaining = market_end - now
                    
                    price = self.feed.get_last_price(asset)
                    if price == 0: continue
                    
                    # Round per asset
                    round_data = self.active_rounds.get(asset)
                    if not round_data: continue

                    # Nuova finestra?
                    if m['id'] != round_data['id']:
                        round_data['id'] = m['id']
                        round_data['placed'] = False
                        
                        # Fetch PTB
                        official_ptb = fetch_official_ptb(m.get('slug'))
                        if official_ptb:
                            round_data['anchor'] = official_ptb
                            source = "OFFICIAL"
                        else:
                            hist = self.feed.get_price_at_time(asset, market_start)
                            round_data['anchor'] = hist if hist > 0 else price
                            source = "BINANCE"
                            
                        log.info(f"🆕 [{asset}] ROUND: {m['title']} | PTB ({source}): ${round_data['anchor']:,.2f}")

                    # Calcolo Delta
                    anchor = round_data['anchor']
                    move_pct = ((price - anchor) / anchor * 100) if anchor > 0 else 0
                    direction = "📈 UP" if move_pct > 0 else "📉 DN" if move_pct < 0 else "➡️ --"
                    
                    # Sniper Logic
                    status = "🎯 READY"
                    if round_data['placed']:
                        status = "✅ BET"
                    elif elapsed < BET_AFTER_SEC:
                        status = "⏳ WAIT"
                    elif remaining < NO_BET_LAST_SEC:
                        status = "⚠️ LATE"
                        round_data['placed'] = True # Non scommettere più
                    
                    # Dashboard data
                    m_ui = m.copy()
                    m_ui.update({
                        "current_price": price,
                        "anchor_price": anchor,
                        "delta": round(move_pct, 4),
                        "status": status,
                        "remaining": int(remaining)
                    })
                    live_games_data.append(m_ui)

                    # Esecuzione scommessa
                    min_signal = config.THRESHOLDS.get(asset, 0.05)
                    
                    if status == "🎯 READY":
                        if abs(move_pct) < min_signal:
                            log.info(f"   ↳ [{asset}] Skip: segnale debole ({move_pct:+.4f}%)")
                        else:
                            side = "UP" if move_pct > 0 else "DOWN"
                            token_bet = m['token_yes'] if side == "UP" else m['token_no']
                            
                            try:
                                resp = requests.get(f"https://clob.polymarket.com/midpoint?token_id={token_bet}", timeout=3)
                                entry_price = float(resp.json().get("mid", 0.50))
                            except: entry_price = 0.50

                            if entry_price > MAX_ENTRY_PRICE:
                                log.warning(f"   ↳ [{asset}] Skip: quota troppo alta ({int(entry_price*100)}¢)")
                                round_data['placed'] = True
                            else:
                                log.info(f"   ↳ 🔥 [{asset}] SNIPING {side} | Delta: {move_pct:+.4f}% | Quota: {int(entry_price*100)}¢")
                                success = self.trader.sniper_trade(m, move_pct)
                                round_data['placed'] = True
                                
                                if success:
                                    save_trade({
                                        "ts": int(now), "market": m['title'], "asset": asset,
                                        "side": side, "movement_pct": round(move_pct, 4),
                                        "entry_price": entry_price, "anchor": anchor,
                                        "market_end": market_end, "condition_id": m.get('conditionId')
                                    })

                # 3. Update Stato UI
                self.state["live_games"] = live_games_data
                self.state["last_update"] = int(now)
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=2)

                # Log sintetico ogni secondo
                summary = " | ".join([f"{g['asset']}: {g['delta']:+.2f}%" for g in live_games_data])
                if summary: print(f"\r[{time.strftime('%H:%M:%S')}] {summary}", end="", flush=True)

            except Exception as e:
                log.error(f"❌ Errore Loop: {e}")

            await asyncio.sleep(1)

if __name__ == "__main__":
    bot = NitroBotPoly()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.feed.stop()
        print("\nChiusura Bot...")
