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
        API_REFRESH_INTERVAL = 15
        
        # Strategia "Sniper a Metà Finestra"
        anchor_price = None        # Prezzo BTC all'inizio della finestra Polymarket
        current_market_id = None   # ID del mercato attuale (per rilevare cambio finestra)
        bet_placed = False         # Già scommesso su questa finestra?
        
        BET_AFTER_SEC = 150        # Scommetti dopo 2:30 min dall'inizio (metà finestra)
        NO_BET_LAST_SEC = 30       # Non scommettere negli ultimi 30 secondi
        
        while self.running:
            try:
                now = time.time()
                
                # 1. Refresh mercato da API (ogni 15s)
                if now - last_api_call > API_REFRESH_INTERVAL:
                    cached_markets = self.watcher.find_btc_markets(limit=20)
                    last_api_call = now
                
                # 2. Prezzo BTC in tempo reale (OGNI SECONDO)
                btc_price = self.feed.get_last_price("BTC")
                
                if not cached_markets:
                    log.info(f"💲 BTC ${btc_price:,.2f} | ⏳ Nessun mercato live. Attendo prossima finestra...")
                    await asyncio.sleep(1)
                    continue
                
                m = cached_markets[0]
                market_start = m['start_timestamp']
                market_end = m['end_timestamp']
                elapsed = now - market_start
                remaining = market_end - now
                
                # 3. Rilevamento nuova finestra → Ancora al prezzo REALE di inizio
                if m['id'] != current_market_id:
                    current_market_id = m['id']
                    bet_placed = False
                    
                    # Recupera prezzo storico al VERO inizio della finestra Polymarket
                    historical_price = self.feed.get_price_at_time("BTC", market_start)
                    if historical_price > 0:
                        anchor_price = historical_price
                        log.info(f"   ⚓ Prezzo Ancorato (STORICO): ${anchor_price:,.2f} (dal buffer Binance)")
                    else:
                        anchor_price = btc_price
                        log.info(f"   ⚓ Prezzo Ancorato (CORRENTE): ${anchor_price:,.2f} (buffer insufficiente)")
                    
                    log.info(f"")
                    log.info(f"{'='*60}")
                    log.info(f"🆕 NUOVA FINESTRA: {m['title']}")
                    log.info(f"   ⚓ Price to Beat: ${anchor_price:,.2f}")
                    log.info(f"   💲 Prezzo Attuale: ${btc_price:,.2f}")
                    log.info(f"   ⏱️  Durata: {int(market_end - market_start)}s | Scade tra {int(remaining)}s")
                    log.info(f"{'='*60}")
                
                # 4. Calcolo movimento DAL PREZZO ANCORATO (non finestra mobile!)
                if anchor_price and anchor_price > 0:
                    movement_pct = ((btc_price - anchor_price) / anchor_price) * 100
                else:
                    movement_pct = 0.0
                
                threshold = config.THRESHOLDS.get("BTC", 0.08)
                direction = "📈 UP" if movement_pct > 0 else "📉 DN" if movement_pct < 0 else "➡️ --"
                
                # Barra progresso finestra
                progress = min(elapsed / (market_end - market_start), 1.0)
                bar_len = 20
                filled = int(progress * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)
                
                log.info(
                    f"💲 ${btc_price:,.2f} | "
                    f"Δ {movement_pct:+.4f}% | "
                    f"{direction} | "
                    f"[{bar}] {int(remaining)}s | "
                    f"{'🎯 PRONTO' if elapsed >= BET_AFTER_SEC and not bet_placed else '⏳ ACCUMULO' if not bet_placed else '✅ PIAZZATA'}"
                )
                
                # 5. DECISIONE DI TRADING
                if not bet_placed:
                    if elapsed < BET_AFTER_SEC:
                        # Fase di accumulo dati - non scommettiamo ancora
                        pass
                    elif remaining < NO_BET_LAST_SEC:
                        # Troppo tardi - rischio di non riuscire a piazzare
                        log.warning(f"   ↳ ⚠️ Troppo tardi per scommettere ({int(remaining)}s rimasti)")
                    elif abs(movement_pct) >= threshold:
                        # SEGNALE FORTE → SCOMMETTI
                        side = "UP (YES)" if movement_pct > 0 else "DOWN (NO)"
                        log.info(f"   ↳ 🎯🎯🎯 SEGNALE CONFERMATO! {side}")
                        log.info(f"   ↳ Movimento: {movement_pct:+.4f}% > Soglia: {threshold}%")
                        log.info(f"   ↳ 🔫 Invio ordine su {m['title']}...")
                        
                        success = self.trader.sniper_trade(m, movement_pct)
                        if success:
                            bet_placed = True
                            self.last_trade_times[m['asset']] = now
                            log.info(f"   ↳ ✅ TRADE ESEGUITO CON SUCCESSO!")
                        else:
                            log.error(f"   ↳ ❌ Trade fallito.")
                    else:
                        pct_of_target = (abs(movement_pct) / threshold) * 100
                        log.info(f"   ↳ ⏳ Segnale debole ({pct_of_target:.0f}% del target). Attendo conferma...")
                
                # 6. Salvataggio stato dashboard
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
