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
        
        while self.running:
            try:
                # 1. Recupero Mercati attivi da Gamma API
                markets = self.watcher.find_btc_markets(limit=20)
                btc_price = self.feed.get_last_price("BTC")
                log.info(f"🔎 [RADAR] Scansione: {len(markets)} mercati trovati | BTC: ${btc_price:,.2f}")
                
                # 2. Recupero Saldi, Posizioni e Storico
                pol, usdc = self.trader.get_balances()
                active_positions = self.trader.get_positions()
                trade_history = self.trader.get_trade_history()
                
                # Protezione Saldo: Se meno di 1.50 USDC.e, sospendi trading
                trading_enabled = usdc >= 1.50
                if not trading_enabled:
                    log.warning(f"⚠️ Saldo Insufficiente: {usdc:.2f} USDC.e. Trading Sospeso.")
                
                # Aggiornamento stato Dashboard
                self.state["wallet"] = {"pol": float(pol), "usdc": float(usdc), "address": self.trader.my_address}
                self.state["active_bets"] = active_positions
                self.state["trade_history"] = trade_history
                self.state["stats"]["total_bets"] = len(active_positions)
                # 3. Analisi e Trading Sniper
                processed_live = []
                for m in markets:
                    try:
                        asset = m['asset']
                        movement = self.watcher.prices.get(asset, 0)
                        threshold = config.THRESHOLDS.get(asset, 0.10)
                        
                        log.debug(f"  > Analisi {m['title']}: Movimento {movement:+.4f}% (Soglia: {threshold}%)")
                        
                        # Controllo Cooldown: Se abbiamo già scommesso su questo asset < 5 min fa, salta
                        last_t = self.last_trade_times.get(asset, 0)
                        if time.time() - last_t < config.COOLDOWN_SECONDS:
                            continue

                        if abs(movement) >= threshold:
                            log.info(f"🎯 SOGLIA SUPERATA [{asset}]: {movement:+.3f}%! Eseguo trade...")
                            
                            # Esecuzione Trade Reale/Simulato
                            success = self.trader.execute_market_trade(m, movement)
                            if success:
                                self.last_trade_times[asset] = time.time()
                                self.state["stats"]["won_bets"] += 1 
                        
                        # Calcolo Odds simulate per la UI
                        odds_yes, odds_no = 1.90, 1.90
                        processed_live.append({
                            "gameId": m['id'],
                            "title": m['title'],
                            "sport": "Crypto",
                            "league": "Polymarket",
                            "volume": m['volume'],
                            "outcomes": [
                                {"outcomeId": m['token_yes'], "name": "YES", "odds": odds_yes},
                                {"outcomeId": m['token_no'], "name": "NO", "odds": odds_no}
                            ]
                        })
                    except: continue
                
                self.state["live_games"] = processed_live
                self.state["wallet"] = {"pol": float(pol), "usdc": float(usdc), "address": self.trader.my_address}
                self.state["last_update"] = int(time.time())
                
                # 4. Update Dashboard Logs
                if processed_live:
                    log_entries = []
                    for m in processed_live:
                        asset = "ETH" # Semplificato per ora
                        mov = self.watcher.prices.get(asset, 0)
                        log_entries.append({
                            "time": int(time.time()),
                            "match": m['title'],
                            "confidence": abs(mov) / 0.10,
                            "recommendation": "BUY YES" if mov > 0 else "BUY NO",
                            "decision": "Analyzing"
                        })
                    self.state["ai_logs"] = (log_entries + self.state["ai_logs"])[:30]
                    
                # Salvataggio Stato
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=2)
                    
            except Exception as e:
                log.error(f"Errore loop bot: {e}")
            
            await asyncio.sleep(5) # Ciclo rapido Sniper Mode

if __name__ == "__main__":
    bot = NitroBotPoly()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        log.info("Chiusura Bot...")
