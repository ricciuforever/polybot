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
    """Controlla gli esiti dei trade passati e ricalcola le statistiche globali."""
    trades = load_trades_log()
    if not trades: 
        return {
            "wins": 0, "losses": 0, "pnl": 0, "volume": 0, "win_rate": 0,
            "recent": []
        }
    
    updated = False
    checked_count = 0
    MAX_CHECKS_PER_RUN = 15 # Limita il numero di chiamate API per evitare rallentamenti thread

    for t in trades:
        if t.get("result") is not None: continue
        if checked_count >= MAX_CHECKS_PER_RUN: break 
        
        # Se il mercato è finito da almeno 2 minuti, controlliamo
        if time.time() > t["market_end"] + 120:
            try:
                cid = t.get("condition_id")
                if not cid: continue
                
                resp = requests.get(f"https://gamma-api.polymarket.com/markets?conditionId={cid}", timeout=5)
                checked_count += 1
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
                            pnl_str = f"+1.00 USDC (WIN)" if t["result"] == "WIN" else f"-1.10 USDC (LOSS)"
                            log.info(f"📊 RISULTATO: {t['market']} -> {t['result']} | {pnl_str}")
                
                time.sleep(0.5) # Piccolo delay antiblocco
            except Exception as e:
                log.warning(f"Errore controllo esito per {t['market']}: {e}")
    
    if updated:
        with open(TRADES_LOG, "w") as f:
            json.dump(trades, f, indent=2)

    # Calcolo statistiche aggiornate
    completed = [t for t in trades if t.get("result") is not None]
    wins = sum(1 for t in completed if t["result"] == "WIN")
    losses = sum(1 for t in completed if t["result"] == "LOSS")
    total = len(completed)
    
    # Stima PNL (1.10 è il costo medio per scommessa da 1.05-1.15 USDC)
    # Una WIN restituisce 1.00 di profitto NETTO (su 1 share)
    # Una LOSS perde l'intero investimento (~1.10 USDC)
    pnl = (wins * 1.0) - (losses * 1.1)
    volume = sum(float(t.get("entry_price", 0.70)) * 1.5 for t in trades) # stima volume CLOB
    win_rate = (wins / total * 100) if total > 0 else 0
    
    return {
        "wins": wins,
        "losses": losses,
        "total": total,
        "pnl": round(pnl, 2),
        "volume": round(volume, 2),
        "win_rate": round(win_rate, 1),
        "recent": sorted(trades, key=lambda x: x.get('ts', 0), reverse=True)[:20]
    }

def extract_ptb_from_text(text):
    """Estrae il prezzo (PTB) dal testo (titolo o descrizione)."""
    if not text: return None
    import re
    # Cerca formati tipo $65,432.10 o 65432.10 o $65432
    patterns = [
        r'\$([0-9,]+(\.[0-9]+)?)', # Con simbolo $
        r'above\s+([0-9,]+(\.[0-9]+)?)', # Dopo "above"
        r'below\s+([0-9,]+(\.[0-9]+)?)'  # Dopo "below"
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            try:
                val_str = match.group(1).replace(',', '')
                return float(val_str)
            except: continue
    return None

class NitroBotPoly:
    def __init__(self):
        self.watcher = PolyWatcher()
        self.feed = BinanceFeed()
        self.trader = PolyTrader()
        self.last_trade_times = {}
        self.running = True
        self.redeem_lock = asyncio.Lock() # Per prevenire esecuzioni multiple contemporanee
        self.state_file = "bot_state.json"
        self.in_progress = set() # Asset attualmente in fase di trade
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

        # === PARAMETRI STRATEGIA MOMENTUM SNIPER ===
        BET_AFTER_SEC = 240        # Entriamo a -60s dalla fine (più aggressivo per prendere quote migliori)
        NO_BET_LAST_SEC = 0        # Nessun ordine limite in chiusura
        REDEEM_INTERVAL = 300      # Auto-redeem ogni 5 MIN (EVITA 429)
        RESULTS_INTERVAL = 300     # Check esiti ogni 5 min
        MIN_SIGNAL = 0.02          # Basta un segnale di direzionalità minima (+/- 0.02%)
        MAX_ENTRY_PRICE = 0.72     # Massimo ingresso a 72c (ROI ~40%)
        MIN_ENTRY_PRICE = 0.65     # Minimo ingresso a 65c (sicurezza che sia in trend forte)
        last_results_check = 0
        last_tp_check = 0
        last_state_save = 0  # Per ridurre I/O su disco
        midpoint_cache = {}  # Per ridurre I/O su rete (quotes)

        while self.running:
            try:
                now = time.time()

                # 1. Refresh mercati (15s) - In thread separato per evitare freeze
                if now - last_api_call > API_REFRESH_INTERVAL:
                    cached_markets = await asyncio.to_thread(self.watcher.find_btc_markets, limit=20)
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

                # 1c. Update esiti e Statistiche (Ogni 5 min) - BACKGROUND TASK
                if now - last_results_check > RESULTS_INTERVAL or last_results_check == 0:
                    async def background_stats():
                        try:
                            # Passiamo i trade recenti per l'aggiornamento
                            res = await asyncio.to_thread(update_trade_results)
                            if res:
                                self.state["stats"] = {
                                    "total": res["total"],
                                    "wins": res["wins"],
                                    "losses": res["losses"],
                                    "pnl": res["pnl"],
                                    "volume": res["volume"],
                                    "win_rate": res["win_rate"]
                                }
                                self.state["recent_trades"] = res["recent"]
                                log.info(f"📈 Stats Dashboard: {res['wins']}W - {res['losses']}L | PNL: ${res['pnl']} | WR: {res['win_rate']}%")
                        except Exception as e:
                            log.error(f"Errore aggiornamento stats: {e}")

                    asyncio.create_task(background_stats())
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
                        
                        # --- NUOVA LOGICA DETERMINAZIONE PTB ---
                        # 1. Prova PTB Ufficiale tramite Endpoint (se disponibile)
                        official_ptb = await asyncio.to_thread(fetch_official_ptb, m.get('slug'))
                        
                        # 2. Prova estrazione da Descrizione (Gamma API)
                        desc_ptb = extract_ptb_from_text(m.get('description'))
                        
                        # 3. Prova estrazione da Titolo/Domanda
                        title_ptb = extract_ptb_from_text(m.get('title'))
                        
                        if official_ptb:
                            anchor_price[asset] = official_ptb
                            ptb_source = "OFFICIAL API"
                        elif desc_ptb:
                            anchor_price[asset] = desc_ptb
                            ptb_source = "DESCRIPTION TEXT"
                        elif title_ptb:
                            anchor_price[asset] = title_ptb
                            ptb_source = "TITLE TEXT"
                        else:
                            # 4. Fallback su Binance Storico (Meno preciso ma meglio di niente)
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
                    bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10)) # Barra più corta per log puliti

                    # Regola di ingaggio
                    enter_threshold = BET_AFTER_SEC 
                    status = "🎯 PRONTO" if remaining <= enter_threshold and len(bet_placed.get(asset, [])) < 1 else "⏳ ACCUMULO" if len(bet_placed.get(asset, [])) < 1 else "✅ PIAZZATA"
                    
                    # LOG FILTRATO: Mostra dettagli ogni 5 secondi, o sempre se siamo negli ultimi 60s
                    if int(now) % 5 == 0 or remaining <= 60 or status == "🎯 PRONTO":
                        log.info(f"💲 {asset} ${asset_price:,.2f} | Δ {movement_pct:+.4f}% | [{bar}] {int(remaining)}s | {status}")

                    live_games_data.append({
                        "id": current_market_id.get(asset, asset),
                        "title": f"[{asset}] {m['title']}",
                        "anchor_price": ap if ap else 0.0,
                        "current_price": asset_price,
                        "volume": 0
                    })

                    # ===== 5. DECISIONE — SMART SNIPER v2 =====
                    if len(bet_placed.get(asset, [])) < 1:
                        if remaining > enter_threshold:
                            pass  # Accumulo
                        elif remaining < NO_BET_LAST_SEC:
                            log.warning(f"   ↳ ⚠️ Troppo tardi ({int(remaining)}s rimasti)")
                            bet_placed[asset] = ["UP", "DOWN"] # Skip permanently for this market
                        else:
                            # Recupero quote con cache di 2 secondi per non saturare CLOB API
                            async def get_cached_midpoint(token_id):
                                cache_key = token_id
                                if cache_key in midpoint_cache:
                                    val, ts = midpoint_cache[cache_key]
                                    if now - ts < 2: return val
                                
                                def _fetch():
                                    try:
                                        r = requests.get("https://clob.polymarket.com/midpoint", params={"token_id": token_id}, timeout=3)
                                        return float(r.json().get("mid", 0.50))
                                    except: return 0.50
                                
                                val = await asyncio.to_thread(_fetch)
                                midpoint_cache[cache_key] = (val, now)
                                return val

                            price_yes = await get_cached_midpoint(m['token_yes'])
                            price_no = await get_cached_midpoint(m['token_no'])

                            # --- NUOVA LOGICA: SEGUE BINANCE NON LE QUOTE ---
                            if movement_pct >= 0.005:
                                side = "UP"
                                entry_price = price_yes
                            elif movement_pct <= -0.005:
                                side = "DOWN"
                                entry_price = price_no
                            else:
                                continue # Trend incerto, non rischiare
                                
                            if asset in self.in_progress:
                                continue # Già in fase di invio ordine

                            cost_c = int(entry_price * 100)
                            profit_c = 100 - cost_c
                            roi = (profit_c / cost_c * 100) if cost_c > 0 else 0

                            if entry_price > MAX_ENTRY_PRICE:
                                pass 
                            elif entry_price < MIN_ENTRY_PRICE:
                                pass 
                            else:
                                log.info(f"   ↳ 📊 Check Mercato: Esito {side} | Quota: {cost_c}¢ (ROI: {roi:.0f}%)")
                                # Pre-lock per evitare corse critiche del loop da 1s
                                self.in_progress.add(asset)
                                log.info(f"   ↳ 🎯 BET {side} (Confidenza ALTISSIMA via Binance: Δ {movement_pct:+.4f}%)")
                                
                                async def bg_trade(market, side, asset, price, ap, asset_p, m_end, m_pct):
                                    try:
                                        log.info(f"   ↳ 🔫 Invio ordine su {market['title']}...")
                                        success = await asyncio.to_thread(self.trader.sniper_trade, market, side, limit_price=MAX_ENTRY_PRICE)

                                        if success:
                                            bet_placed[asset].append(side)
                                            self.last_trade_times[asset] = time.time()
                                            log.info(f"   ↳ ✅ 💰 TRADE ESEGUITO SU {market['title']} | Prezzo Ingr.: {int(price*100)}¢ | Direzione: {side}")

                                            entry = {
                                                "ts": int(time.time()),
                                                "market": market['title'],
                                                "side": side,
                                                "movement_pct": round(m_pct, 4),
                                                "entry_price": price,
                                                "anchor": ap,
                                                "asset_at_bet": asset_p,
                                                "market_end": m_end,
                                                "condition_id": market.get('conditionId'),
                                                "result": None
                                            }
                                            save_trade(entry)
                                            self.state["recent_trades"] = [entry] + self.state["recent_trades"][:9]
                                        else:
                                            log.error(f"   ↳ ❌ Trade fallito per {market['title']}.")
                                    except Exception as e:
                                        log.error(f"❌ Errore critico in bg_trade: {e}")
                                    finally:
                                        self.in_progress.remove(asset)

                                asyncio.create_task(bg_trade(m, side, asset, entry_price, ap, asset_price, market_end, movement_pct))

                # La vendita anticipata (Take Profit) è stata rimossa. 
                # Con la nuova strategia "Sure Win", deteniamo la posizione fino
                # a risoluzione (~5 min) e incassiamo tramite auto-redeem.


                # 6. Stato dashboard (Salvataggio ogni 5s per ridurre I/O su disco)
                if now - last_state_save > 5:
                    self.state["live_games"] = live_games_data
                    self.state["last_update"] = int(now)
                    temp_file = self.state_file + ".tmp"
                    with open(temp_file, "w") as f:
                        json.dump(self.state, f, indent=2)
                    import os
                    os.replace(temp_file, self.state_file)
                    last_state_save = now

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
