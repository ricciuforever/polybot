import requests
import config
import re
import time
import json
from modules.logger import get_logger

log = get_logger("azuro_watcher")

class AzuroWatcher:
    def __init__(self):
        self.base_url = config.AZURO_REST_API
        # Keywords generiche per intercettare i mercati Prediction
        self.keywords = ["up or down", "up/down", "price"]

    def find_market(self, asset: str):
        """Scansiona i mercati direttamente tramite le API di DGPredict per trovare i 5m."""
        
        # Mapping asset per la ricerca nel question/slug (Espanso per DGPredict)
        asset_map = {
            "BTC": ["btc", "bitcoin"],
            "ETH": ["eth", "ethereum"],
            "XRP": ["xrp", "ripple"],
            "SOL": ["sol", "solana"],
            "DOGE": ["doge", "dogecoin"]
        }
        search_kws = asset_map.get(asset, [asset.lower()])

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://dgpredict.com/app/crypto"
        }

        # Query dei mercati a 5 minuti (torniamo a volume24hr che è garantito, limit 100 basta per trovarli tutti)
        url = "https://dgpredict.com/app/api/markets?limit=100&offset=0&active=true&closed=false&tag_slug=5M&order=volume24hr&ascending=false"
        
        current_time = int(time.time()) #
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                log.error(f"Errore API DGPredict: {resp.status_code}")
                return None
            
            data = resp.json()
            markets = data.get("markets", [])
            
            import calendar
            import re
            
            valid_markets = []
            
            for m in markets:
                question = m.get("question", "").lower()
                slug = m.get("slug", "").lower()
                
                # 1. Recupero tempi UTC assoluti direttamente dallo slug (bypassando il fuso orario locale del SO)
                slug_match = re.search(r'-(\d{10})$', slug)
                if slug_match:
                    market_end_ts = int(slug_match.group(1))
                else:
                    market_end_ts = calendar.timegm(time.strptime(m["endTime"][:19], "%Y-%m-%dT%H:%M:%S"))
                    
                market_start_ts = market_end_ts - 300 
                
                # 2. FILTRO TEMPORALE STRINGENTE
                # current_time deve essere almeno 60 secondi PRIMA dell'inizio del mercato
                # Se mancano meno di 60s, il rischio di "Rejection" dal relayer è troppo alto.
                if current_time >= (market_start_ts - 60):
                    continue

                # 3. FILTRO "ROBA DI IERI" (Sicurezza extra)
                # Se il mercato finisce più di 12 ore nel futuro o è nel passato, scarta.
                if market_end_ts < current_time or market_end_ts > (current_time + 43200):
                    continue
                
                asset_match = any(kw in question or kw in slug for kw in search_kws)
                
                if asset_match:
                    outcomes = m.get("outcomes", [])
                    if not outcomes: continue
                    
                    main_outcome = outcomes[0]
                    cond_id = main_outcome.get("conditionId")
                    core_addr = main_outcome.get("coreAddress") or m.get("coreAddress")
                    
                    if cond_id:
                        price_up = float(main_outcome.get("priceYes", 50))
                        price_down = 100.0 - price_up
                        
                        odds = {
                            "1": 100.0 / price_up if price_up > 0 else 1.0,
                            "2": 100.0 / price_down if price_down > 0 else 1.0
                        }
                        
                        valid_markets.append({
                            "conditionId": cond_id,
                            "title": m["question"],
                            "startsAt": market_start_ts, # Usiamo l'inizio reale
                            "outcomes": odds,
                            "gameId": m["id"],
                            "core": core_addr
                        })
            
            # Seleziona il mercato valido PIU' IMMINENTE
            if valid_markets:
                valid_markets.sort(key=lambda x: x["startsAt"])
                best_market = valid_markets[0]
                log.info(f"🎯 MERCATO VALIDO TROVATO: {best_market['title']}")
                return best_market
        except Exception as e:
            log.error(f"Errore scansione DGPredict {asset}: {e}")
        
        return None