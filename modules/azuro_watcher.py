import requests
import config
import re
import time
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

        # Query dei mercati a 5 minuti (tag_slug=5M)
        url = "https://dgpredict.com/app/api/markets?limit=48&offset=0&active=true&archived=false&closed=false&tag_slug=5M&order=volume24hr&ascending=false"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                log.error(f"Errore API DGPredict: {resp.status_code}")
                return None
            
            data = resp.json()
            markets = data.get("markets", [])
            
            for m in markets:
                question = m.get("question", "").lower()
                slug = m.get("slug", "").lower()
                
                # Match di una qualsiasi delle keyword nell'asset (titolo o slug)
                asset_match = any(kw in question or kw in slug for kw in search_kws)
                
                if asset_match:
                    # Estraiamo gli outcomes e i conditionId
                    # Il primo outcome è solitamente "Up" (Sì)
                    outcomes = m.get("outcomes", [])
                    if not outcomes: continue
                    
                    # DGPredict usa USDC.e, mappiamo i prezzi in quote (Odds)
                    # Odds = 100 / price_yes
                    main_outcome = outcomes[0]
                    cond_id = main_outcome.get("conditionId")
                    
                    if cond_id:
                        log.info(f"🎯 MERCATO DGP [GEM] TROVATO: {m['question']}")
                        # Azuro V3 Outcome IDs: 1 (UP/Yes), 2 (DOWN/No)
                        price_up = float(main_outcome.get("priceYes", 50))
                        price_down = 100.0 - price_up
                        
                        odds = {
                            "1": 100.0 / price_up if price_up > 0 else 1.0,
                            "2": 100.0 / price_down if price_down > 0 else 1.0
                        }
                        
                        return {
                            "conditionId": cond_id,
                            "title": m["question"],
                            "startsAt": int(time.mktime(time.strptime(m["endTime"][:19], "%Y-%m-%dT%H:%M:%S"))),
                            "outcomes": odds,
                            "gameId": m["id"]
                        }
        except Exception as e:
            log.error(f"Errore scansione DGPredict {asset}: {e}")
        
        return None