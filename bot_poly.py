import asyncio
import time
import json
import os
import requests
from modules.poly_watcher import PolyWatcher
from modules.price_feed import BinanceFeed
from poly_trader import PolyTrader
import config
from modules.http_utils import apply_ip_binding
apply_ip_binding()
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
            # Supponendo che il JSON contenga il valore in un campo 'price' o simile
            # In base alla documentazione fornita, estraiamo il valore numerico
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
                            t["result"] = "WIN" if t["side"] == actual_side else "LOSS"
                            t["payout"] = 1.0 if t["result"] == "WIN" else 0.0
                            updated = True
                            pnl = "+1.00 USDC" if t["result"] == "WIN" else "-1.10 USDC" # stima approx
                            log.info(f"📊 💰 RISULTATO CHIUSURA TRADE: {t['market']} -> {t['result']} ({actual_side}) | PNL: {pnl}")
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
        self.redeem_lock = asyncio.Lock() # Per prevenire esecuzioni multiple contemporanee
        self.bet_size = config.BET_SIZE
        self.state_file = "bot_state.json"
        self.state = {
            "last_update": 0, "live_games": [], "ai_logs": [],
            "wallet": {"pol": 0, "usdc": 0, "address": self.trader.my_address},
            "stats": {"total_bets": 0, "won_bets": 0},
            "recent_trades": []
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

        anchor_price = {}
        current_market_id = {}
        bet_placed = {} # dict of asset -> list of sides bought
        last_redeem_check = 0

        # === PARAMETRI STRATEGIA DOUBLE BUY (REVERSE HEDGING) ===
        BET_AFTER_SEC = 150        # Entriamo da metà partita (150s) per seguire il trend o copririci se inverte
        NO_BET_LAST_SEC = 0        # Nessun ordine negli ultimi 0s, operativo per hedging fino all'ultimissimo secondo
        REDEEM_INTERVAL = 300      # Auto-redeem ogni 5 MIN (EVITA 429)
        RESULTS_INTERVAL = 300     # Check esiti ogni 5 min
        MIN_SIGNAL = 0.02          # Basta un segnale di direzionalità minima (+/- 0.02%)
        MAX_ENTRY_PRICE = 0.58     # Acquistiamo fno a 58c. Molto margine per cross-over in caso di hedging
        MIN_ENTRY_PRICE = 0.42     # Acquistiamo già da 42c se il favor sta arrivando dal basso
        last_results_check = 0
        last_tp_check = 0

        while self.running:
            try:
                now = time.time()

                # 1. Refresh mercati (15s)
                if now - last_api_call > API_REFRESH_INTERVAL:
                    cached_markets = self.watcher.find_btc_markets(limit=20)
                    last_api_call = now

                # 1b. Aggiornamento saldi (5 min) - Veloce, NON BLOCCANTE
                if now - last_redeem_check > REDEEM_INTERVAL:
                    async def background_redeem():
                        if self.redeem_lock.locked(): return
                        async with self.redeem_lock:
                            try:
                                await asyncio.to_thread(self.trader.auto_redeem)
                                pol, usdc = await asyncio.to_thread(self.trader.get_balances)
                                if usdc is not None:
                                    self.state["wallet"] = {"pol": float(pol), "usdc": float(usdc), "address": self.trader.my_address}
                            except Exception as e:
                                log.error(f"Errore update saldi bg: {e}")
                                
                    asyncio.create_task(background_redeem())
                    last_redeem_check = now

                # 1c. Update esiti (300s)
                if now - last_results_check > RESULTS_INTERVAL:
                    if update_trade_results():
                        # Ricalcola stats e recent_trades per dashboard
                        trades = load_trades_log()
                        comp = [t for t in trades if t.get("result") is not None]
                        wins = sum(1 for t in comp if t["result"] == "WIN")
                        self.state["stats"] = {"total_bets": len(comp), "won_bets": wins}
                        self.state["recent_trades"] = sorted(trades, key=lambda x: x.get('ts', 0), reverse=True)[:10]
                        log.info(f"📈 Stats Aggiornate: {wins}W - {len(comp)-wins}L")
                    last_results_check = now

                if not cached_markets:
                    prices_log = []
                    for asset in config.ASSETS:
                        p = self.feed.get_last_price(asset)
                        if p > 0: prices_log.append(f"{asset} ${p:,.2f}" if p >= 1 else f"{asset} ${p:,.4f}")
                    
                    price_str = " | ".join(prices_log)
                    if price_str: log.info(f"💲 {price_str} | ⏳ Nessun mercato <= 7m trovato al momento.")
                    self.state["live_games"] = []
                    await asyncio.sleep(1)
                    continue

                live_games_data = []
                # Loop su tutti i mercati (es. BTC e ETH simultaneamente)
                for m in cached_markets:
                    asset = m.get('asset', 'BTC')
                    asset_price = self.feed.get_last_price(asset)

                    if asset_price == 0:
                        continue

                    market_start = m['start_timestamp']
                    market_end = m['end_timestamp']
                    elapsed = now - market_start
                    remaining = market_end - now

                    # 3. Nuova finestra -> Ancora prezzo
                    if m['id'] != current_market_id.get(asset):
                        current_market_id[asset] = m['id']
                        bet_placed[asset] = []
                        
                        # Prova prima il PTB Ufficiale
                        official_ptb = fetch_official_ptb(m.get('slug'))
                        
                        if official_ptb:
                            anchor_price[asset] = official_ptb
                            ptb_source = "OFFICIAL API"
                        else:
                            # Fallback su Binance Storico
                            historical_price = self.feed.get_price_at_time(asset, market_start)
                            anchor_price[asset] = historical_price if historical_price > 0 else asset_price
                            ptb_source = "BINANCE FALLBACK"
                        
                        log.info(f"")
                        log.info(f"{'='*60}")
                        log.info(f"🆕 NUOVA FINESTRA {asset}: {m['title']}")
                        log.info(f"   ⚓ Price to Beat ({ptb_source}): ${anchor_price[asset]:,.2f}")
                        log.info(f"   💲 Prezzo Attuale {asset}: ${asset_price:,.2f}")
                        log.info(f"   ⏱️  Durata: {int(market_end - market_start)}s | Scade tra {int(remaining)}s")
                        log.info(f"{'='*60}")

                    # 4. Movimento dal Price to Beat
                    ap = anchor_price.get(asset)
                    if ap and ap > 0:
                        movement_pct = ((asset_price - ap) / ap) * 100
                    else:
                        movement_pct = 0.0

                    direction = "📈 UP" if movement_pct > 0 else "📉 DN" if movement_pct < 0 else "➡️ --"

                    # Barra progresso
                    duration = market_end - market_start
                    progress = min(elapsed / duration, 1.0) if duration > 0 else 1.0
                    bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))

                    # Regola di ingaggio: Entra solo negli ultimi 60 secondi della finestra
                    # Anche se Polymarket dà startDate vecchie, noi sappiamo che il bucket è di 300s.
                    enter_threshold = BET_AFTER_SEC 
                    
                    status = "🎯 PRONTO" if remaining <= enter_threshold and len(bet_placed.get(asset, [])) < 2 else "⏳ ACCUMULO" if len(bet_placed.get(asset, [])) < 2 else "✅ PIAZZATA"
                    log.info(f"💲 {asset} ${asset_price:,.2f} | Δ {movement_pct:+.4f}% | {direction} | [{bar}] {int(remaining)}s | {status}")

                    live_games_data.append({
                        "id": current_market_id.get(asset, asset),
                        "title": f"[{asset}] {m['title']}",
                        "anchor_price": ap if ap else 0.0,
                        "current_price": asset_price,
                        "volume": 0
                    })

                    # ===== 5. DECISIONE — SMART SNIPER v2 =====
                    if len(bet_placed.get(asset, [])) < 2:
                        if remaining > enter_threshold:
                            pass  # Accumulo
                        elif remaining < NO_BET_LAST_SEC:
                            log.warning(f"   ↳ ⚠️ Troppo tardi ({int(remaining)}s rimasti)")
                            bet_placed[asset] = ["UP", "DOWN"] # Skip permanently for this market
                        else:
                            # Verifica indipendente della probabilità dal mercato Polymarket
                            try:
                                resp_y = requests.get("https://clob.polymarket.com/midpoint", params={"token_id": m['token_yes']}, timeout=3)
                                price_yes = float(resp_y.json().get("mid", 0.50))
                            except: price_yes = 0.50
                            
                            try:
                                resp_n = requests.get("https://clob.polymarket.com/midpoint", params={"token_id": m['token_no']}, timeout=3)
                                price_no = float(resp_n.json().get("mid", 0.50))
                            except: price_no = 0.50

                            if price_yes >= price_no:
                                side = "UP"
                                entry_price = price_yes
                            else:
                                side = "DOWN"
                                entry_price = price_no
                                
                            if side in bet_placed.get(asset, []):
                                continue # Già comprato questo lato

                            cost_c = int(entry_price * 100)
                            profit_c = 100 - cost_c
                            roi = (profit_c / cost_c * 100) if cost_c > 0 else 0

                            log.info(f"   ↳ 📊 Check Mercato: Esito Favorito -> {side} | Quota: {cost_c}¢ (ROI: {roi:.0f}%)")

                            if entry_price > MAX_ENTRY_PRICE:
                                log.warning(f"   ↳ ⚠️ Quota {cost_c}¢ > {round(MAX_ENTRY_PRICE*100)}¢. Guadagno troppo esiguo. ATTESA.")
                                pass 
                            elif entry_price < MIN_ENTRY_PRICE:
                                log.warning(f"   ↳ ⚠️ Quota {cost_c}¢ < {round(MIN_ENTRY_PRICE*100)}¢. Probabilità ancora troppo bassa. ATTESA.")
                                pass 
                            else:
                                # Anti-PingPong: Se stiamo per fare hedging (seconda bet), attendiamo che il trend sia confermato
                                # e non sia solo una micro-oscillazione sull'equatore 0.50.
                                if len(bet_placed.get(asset, [])) == 1:
                                    last_t = self.last_trade_times.get(asset, 0)
                                    if now - last_t < 15:
                                        log.warning(f"   ↳ ⚠️ MICRO-OSCILLAZIONE. Attesa 15s prima di hedgare...")
                                        continue
                                log.info(f"   ↳ 🎯 BET {side} (Confidenza ALTISSIMA: {cost_c}%)")
                                log.info(f"   ↳ 🔫 Invio ordine su {m['title']}...")

                                success = self.trader.sniper_trade(m, side, limit_price=MAX_ENTRY_PRICE)

                                if success:
                                    bet_placed[asset].append(side)
                                    self.last_trade_times[asset] = now
                                    log.info(f"   ↳ ✅ 💰 TRADE ESEGUITO SU {m['title']} | Prezzo Ingr.: {cost_c}¢ | Direzione: {side}")

                                    # Tracking
                                    entry = {
                                        "ts": int(now),
                                        "market": m['title'],
                                        "side": side,
                                        "movement_pct": round(movement_pct, 4),
                                        "entry_price": entry_price,
                                        "anchor": ap,
                                        "asset_at_bet": asset_price,
                                        "market_end": market_end,
                                        "condition_id": m.get('conditionId'),
                                        "result": None
                                    }
                                    save_trade(entry)
                                    self.state["recent_trades"] = [entry] + self.state["recent_trades"][:9]
                                else:
                                    log.error(f"   ↳ ❌ Trade fallito.")

                # La vendita anticipata (Take Profit) è stata rimossa. 
                # Con la nuova strategia "Sure Win", deteniamo la posizione fino
                # a risoluzione (~5 min) e incassiamo tramite auto-redeem.


                # 6. Stato dashboard
                self.state["live_games"] = live_games_data
                self.state["last_update"] = int(now)
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=2)

            except Exception as e:
                log.error(f"❌ Errore loop: {e}")

            await asyncio.sleep(1)

def kill_zombies():
    import subprocess
    import os
    my_pid = str(os.getpid())
    try:
        if os.name == 'nt': # Windows
            cmd = 'wmic process where "name like \'%python%\'" get commandline,processid'
            output = subprocess.check_output(cmd, shell=True, text=True)
            for line in output.splitlines():
                if 'bot_poly.py' in line and my_pid not in line:
                    parts = line.strip().split()
                    if parts:
                        zombie_pid = parts[-1]
                        if zombie_pid.isdigit() and zombie_pid != my_pid:
                            log.warning(f"🧟 Trovata istanza zombie del bot (PID {zombie_pid}). La uccido...")
                            subprocess.run(f"taskkill /PID {zombie_pid} /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else: # Linux/Mac
            cmd = "ps -eo pid,command"
            output = subprocess.check_output(cmd, shell=True, text=True)
            for line in output.splitlines():
                if 'bot_poly.py' in line and my_pid not in line:
                    parts = line.strip().split()
                    if parts:
                        zombie_pid = parts[0]
                        if zombie_pid.isdigit() and zombie_pid != my_pid:
                            log.warning(f"🧟 Trovata istanza zombie del bot (PID {zombie_pid}). La uccido...")
                            subprocess.run(f"kill -9 {zombie_pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log.error(f"Errore controllo zombie: {e}")

if __name__ == "__main__":
    kill_zombies()
    
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
        log.info("Chiusura Bot forzata... Bye!")
        try: bot.feed.stop() 
        except: pass
        os._exit(0)
