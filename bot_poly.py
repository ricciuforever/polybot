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
                # Recupera l'esito dal mercato tramite condition_id
                cid = t.get("condition_id")
                if not cid: continue
                
                resp = requests.get(f"https://gamma-api.polymarket.com/markets?conditionId={cid}", timeout=5)
                if resp.status_code == 200 and resp.json():
                    m = resp.json()[0]
                    if m.get("closed"):
                        prices = m.get("outcomePrices") # ES: ["0", "1"]
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
        self.state = {
            "last_update": 0, "live_games": [], "ai_logs": [],
            "wallet": {"pol": 0, "usdc": 0, "address": self.trader.my_address},
            "stats": {"total_bets": 0, "won_bets": 0}
        }

    async def run(self):
        log.info("🚀 NitroBot POLYMARKET (Smart Sniper v2) Avviato!")
        log.info(f"Monitoraggio Asset: {', '.join(config.ASSETS)}")
        log.info(f"Wallet: {self.trader.my_address}")

        self.feed.start()
        log.info("Attendo warm-up feed Binance...")
        await asyncio.sleep(5)

        cached_markets = []
        last_api_call = 0
        API_REFRESH_INTERVAL = 15

        anchor_price = None
        current_market_id = None
        bet_placed = False
        last_redeem_check = 0

        # === PARAMETRI STRATEGIA SMART SNIPER v2 ===
        BET_AFTER_SEC = 150        # Scommetti dopo 2:30 min
        NO_BET_LAST_SEC = 30       # Stop ultimi 30 sec
        REDEEM_INTERVAL = 30       # Auto-redeem ogni 30s
        RESULTS_INTERVAL = 300     # Check esiti ogni 5 min
        MIN_SIGNAL = 0.02          # Skip se |delta| < 0.02% (rumore)
        MAX_ENTRY_PRICE = 0.65     # Non comprare sopra 65c (ROI minimo 54%)
        last_results_check = 0

        while self.running:
            try:
                now = time.time()

                # 1. Refresh mercati (15s)
                if now - last_api_call > API_REFRESH_INTERVAL:
                    cached_markets = self.watcher.find_btc_markets(limit=20)
                    last_api_call = now

                # 1b. Auto-redeem + saldo (30s)
                if now - last_redeem_check > REDEEM_INTERVAL:
                    redeemed = self.trader.auto_redeem()
                    pol, usdc = self.trader.get_balances()
                    self.state["wallet"] = {"pol": float(pol), "usdc": float(usdc), "address": self.trader.my_address}
                    
                    if redeemed:
                        log.info(f"💰 Riscattate {redeemed} posizioni! Saldo: ${usdc:.2f} USDC")
                    elif usdc < 1.05:
                        log.warning(f"💰 Saldo: ${usdc:.2f} USDC | ⚠️ Sotto soglia minima")
                    last_redeem_check = now

                # 1c. Update esiti (300s)
                if now - last_results_check > RESULTS_INTERVAL:
                    if update_trade_results():
                        # Ricalcola stats per dashboard
                        trades = load_trades_log()
                        comp = [t for t in trades if t.get("result") is not None]
                        wins = sum(1 for t in comp if t["result"] == "WIN")
                        self.state["stats"] = {"total_bets": len(comp), "won_bets": wins}
                        log.info(f"📈 Stats Aggiornate: {wins}W - {len(comp)-wins}L")
                    last_results_check = now

                # 2. Prezzo BTC
                btc_price = self.feed.get_last_price("BTC")

                if not cached_markets:
                    log.info(f"💲 BTC ${btc_price:,.2f} | ⏳ Nessun mercato live.")
                    await asyncio.sleep(1)
                    continue

                m = cached_markets[0]
                market_start = m['start_timestamp']
                market_end = m['end_timestamp']
                elapsed = now - market_start
                remaining = market_end - now

                # 3. Nuova finestra -> Ancora prezzo
                if m['id'] != current_market_id:
                    current_market_id = m['id']
                    bet_placed = False

                    historical_price = self.feed.get_price_at_time("BTC", market_start)
                    anchor_price = historical_price if historical_price > 0 else btc_price

                    log.info(f"")
                    log.info(f"{'='*60}")
                    log.info(f"🆕 NUOVA FINESTRA: {m['title']}")
                    log.info(f"   ⚓ Price to Beat: ${anchor_price:,.2f}")
                    log.info(f"   💲 Prezzo Attuale: ${btc_price:,.2f}")
                    log.info(f"   ⏱️  Durata: {int(market_end - market_start)}s | Scade tra {int(remaining)}s")
                    log.info(f"{'='*60}")

                # 4. Movimento dal Price to Beat
                if anchor_price and anchor_price > 0:
                    movement_pct = ((btc_price - anchor_price) / anchor_price) * 100
                else:
                    movement_pct = 0.0

                direction = "📈 UP" if movement_pct > 0 else "📉 DN" if movement_pct < 0 else "➡️ --"

                # Barra progresso
                progress = min(elapsed / (market_end - market_start), 1.0)
                bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))

                status = "🎯 PRONTO" if elapsed >= BET_AFTER_SEC and not bet_placed else "⏳ ACCUMULO" if not bet_placed else "✅ PIAZZATA"
                log.info(f"💲 ${btc_price:,.2f} | Δ {movement_pct:+.4f}% | {direction} | [{bar}] {int(remaining)}s | {status}")

                # ===== 5. DECISIONE — SMART SNIPER v2 =====
                if not bet_placed:
                    if elapsed < BET_AFTER_SEC:
                        pass  # Accumulo
                    elif remaining < NO_BET_LAST_SEC:
                        log.warning(f"   ↳ ⚠️ Troppo tardi ({int(remaining)}s rimasti)")
                        bet_placed = True
                    elif abs(movement_pct) < MIN_SIGNAL:
                        # SEGNALE TROPPO DEBOLE -> Skip (evita coin flip con fee negative)
                        log.info(f"   ↳ 🔇 Segnale debole ({movement_pct:+.4f}% < {MIN_SIGNAL}%). SKIP.")
                    else:
                        # SEGNALE VALIDO -> Recupero odds mercato
                        if movement_pct > 0:
                            side = "UP"
                            token_bet = m['token_yes']
                        else:
                            side = "DOWN"
                            token_bet = m['token_no']

                        # Midpoint del token che vogliamo comprare
                        try:
                            resp = requests.get("https://clob.polymarket.com/midpoint",
                                params={"token_id": token_bet}, timeout=3)
                            entry_price = float(resp.json().get("mid", 0.50))
                        except:
                            entry_price = 0.50

                        cost_c = int(entry_price * 100)
                        profit_c = 100 - cost_c
                        roi = (profit_c / cost_c * 100) if cost_c > 0 else 0

                        # Il mercato conferma? Se compriamo a <50c = mercato pensa il contrario = noi vediamo prima
                        market_agrees = entry_price < 0.50

                        log.info(f"   ↳ 📊 Segnale: {side} | Δ {movement_pct:+.4f}%")
                        log.info(f"   ↳ 📊 Quota: {cost_c}¢ → Payout: {profit_c}¢ (ROI: {roi:.0f}%)")

                        if entry_price > MAX_ENTRY_PRICE:
                            log.warning(f"   ↳ ⚠️ Quota {cost_c}¢ > {int(MAX_ENTRY_PRICE*100)}¢. Payout troppo basso. SKIP.")
                            bet_placed = True
                        else:
                            confidence = "FORTE 🔥" if market_agrees else "BUONA"
                            log.info(f"   ↳ 🎯 BET {side} (confidenza: {confidence})")
                            log.info(f"   ↳ 🔫 Invio ordine su {m['title']}...")

                            success = self.trader.sniper_trade(m, movement_pct)
                            bet_placed = True

                            if success:
                                self.last_trade_times[m['asset']] = now
                                log.info(f"   ↳ ✅ TRADE ESEGUITO!")

                                # Tracking
                                save_trade({
                                    "ts": int(now),
                                    "market": m['title'],
                                    "side": side,
                                    "movement_pct": round(movement_pct, 4),
                                    "entry_price": entry_price,
                                    "anchor": anchor_price,
                                    "btc_at_bet": btc_price,
                                    "market_end": market_end,
                                    "condition_id": m.get('conditionId'),
                                    "result": None
                                })
                            else:
                                log.error(f"   ↳ ❌ Trade fallito.")

                # 6. Stato dashboard
                self.state["last_update"] = int(now)
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=2)

            except Exception as e:
                log.error(f"❌ Errore loop: {e}")

            await asyncio.sleep(1)

if __name__ == "__main__":
    # Statistiche all'avvio
    trades = load_trades_log()
    if trades:
        completed = [t for t in trades if t.get("result") is not None]
        if completed:
            wins = sum(1 for t in completed if t["result"] == "WIN")
            log.info(f"📈 Storico: {len(completed)} trades | {wins}W/{len(completed)-wins}L | Win rate: {wins/len(completed)*100:.0f}%")

    bot = NitroBotPoly()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.feed.stop()
        log.info("Chiusura Bot... Bye!")
