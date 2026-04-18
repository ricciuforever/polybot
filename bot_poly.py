import asyncio
import time
import json
import os
from modules.poly_watcher import PolyWatcher
from modules.price_feed import BinanceFeed
from poly_trader import PolyTrader
import config
from modules.logger import get_logger

log = get_logger("bot_poly")

class NitroBotPoly:
    def __init__(self):
        self.watcher = PolyWatcher()
        self.feed = BinanceFeed()
        self.trader = PolyTrader()
        self.last_trade_times = {}
        self.running = True
        self.bet_size = config.BET_SIZE
        self.processed_markets = set()
        self.state_file = "bot_state.json"
        
        # Stato Iniziale Dashboard
        self.state = {
            "last_update": 0,
            "live_games": [],
            "ai_logs": [],
            "wallet": {"pol": 0, "usdc": 0, "address": self.trader.my_address},
            "stats": {"total_bets": 0, "won_bets": 0}
        }

    async def run(self):
        log.info("🚀 NitroBot POLYMARKET (Threshold Mode) Avviato!")
        log.info(f"Monitoraggio Asset: {', '.join(config.ASSETS)}")
        log.info(f"Wallet: {self.trader.my_address}")
        
        # Avvio Feed Prezzi
        self.feed.start()
        log.info("Attendo warm-up feed Binance...")
        await asyncio.sleep(5)
        
        cached_markets = []
        last_api_call = 0
        API_REFRESH_INTERVAL = 30 # Aggiorna mercato ogni 30s (tanto dura 5 min)
        
        while self.running:
            try:
                now = time.time()
                
                # 1. Refresh mercato da API (ogni 30s)
                if now - last_api_call > API_REFRESH_INTERVAL:
                    cached_markets = self.watcher.find_btc_markets(limit=20)
                    last_api_call = now
                    pol, usdc = self.trader.get_balances()
                    self.state["wallet"] = {"pol": float(pol), "usdc": float(usdc), "address": self.trader.my_address}
                    if cached_markets:
                        log.info(f"📡 [API] Mercato Live: {cached_markets[0]['title']}")
                    else:
                        log.info(f"📡 [API] Nessun mercato BTC 5m live al momento.")
                
                # 2. Log prezzo + movimento OGNI SECONDO
                btc_price = self.feed.get_last_price("BTC")
                movement = self.feed.get_window_movement("BTC")
                threshold = config.THRESHOLDS.get("BTC", 0.10)
                direction = "📈 UP" if movement > 0 else "📉 DOWN" if movement < 0 else "➡️ FLAT"
                
                log.info(f"💲 BTC ${btc_price:,.2f} | Mov: {movement:+.4f}% | Soglia: {threshold}% | {direction}")
                
                # 3. Valutazione trade (solo se abbiamo un mercato live)
                if cached_markets:
                    m = cached_markets[0]
                    asset = m['asset']
                    
                    # Cooldown check
                    last_t = self.last_trade_times.get(asset, 0)
                    time_left = config.COOLDOWN_SECONDS - (now - last_t)
                    
                    if time_left > 0:
                        log.info(f"   ↳ ⏳ Cooldown attivo: {int(time_left)}s rimanenti")
                    elif abs(movement) >= threshold:
                        side = "UP (YES)" if movement > 0 else "DOWN (NO)"
                        log.info(f"   ↳ 🎯 SEGNALE! {side} | Mov {movement:+.4f}% > Soglia {threshold}%")
                        log.info(f"   ↳ 🔫 Invio ordine su {m['title']}...")
                        success = self.trader.execute_market_trade(m, movement)
                        if success:
                            self.last_trade_times[asset] = now
                            self.state["stats"]["won_bets"] += 1
                            log.info(f"   ↳ ✅ TRADE ESEGUITO!")
                        else:
                            log.error(f"   ↳ ❌ Trade fallito.")
                    else:
                        pct = (abs(movement) / threshold) * 100
                        log.info(f"   ↳ ⏳ Sotto soglia ({pct:.0f}% del target). Attendo...")
                
                # 4. Salvataggio stato dashboard
                self.state["last_update"] = int(now)
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=2)
                    
            except Exception as e:
                log.error(f"❌ Errore loop: {e}")
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    bot = NitroBotPoly()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.feed.stop()
        log.info("Chiusura Bot... Bye!")
