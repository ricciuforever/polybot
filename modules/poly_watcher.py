import requests
import json
import logging
from typing import List, Dict, Any
import config

log = logging.getLogger("poly_watcher")

class PolyWatcher:
    """Monitora i mercati Polymarket tramite Gamma API con scansione massiva e filtraggio locale."""
    
    def __init__(self, clob_client=None):
        self.url = config.POLY_GAMMA_URL
        self.crypto_keywords = {
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth"],
            "DOGE": ["dogecoin", "doge"],
            "SOL": ["solana", "sol"],
            "XRP": ["ripple", "xrp"]
        }

    def find_btc_markets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Trova i mercati crypto attivi scansionando i top 500 mercati per volume."""
        endpoint = f"{self.url}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100,
            "search": "btc-updown-5m"
        }
        
        all_found = []
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            if resp.status_code != 200:
                log.error(f"Errore Gamma API: {resp.status_code}")
                return []
            
            data = resp.json()
            log.info(f"📡 Gamma API: Ricevuti {len(data)} mercati da analizzare.")
            for m in data:
                q = m.get('question', '').lower()
                
                # Identifica l'asset
                matched_asset = None
                for asset, aliases in self.crypto_keywords.items():
                    if any(alias in q for alias in aliases):
                        matched_asset = asset
                        break
                
                if matched_asset:
                    # Filtro Sniper Matematico + Filtro Imminenza
                    import re
                    from datetime import datetime
                    times = re.findall(r"(\d+):(\d+)", q)
                    is_real_5m = False
                    is_imminent = False
                    
                    if len(times) >= 2:
                        try:
                            h1, m1 = map(int, times[0])
                            h2, m2 = map(int, times[1])
                            duration = abs((h2 * 60 + m2) - (h1 * 60 + m1))
                            if duration == 5 or duration == 1435:
                                is_real_5m = True
                            is_imminent = True # Mostriamo tutto ciò che inizia nelle prossime 24 ore
                        except: pass
                    
                    clob_ids = m.get('clobTokenIds')
                    if clob_ids:
                        try:
                            tokens = json.loads(clob_ids)
                            is_crypto_target = any(x in q for x in ["up or down", "price of", "bitcoin", "btc"])
                            
                            if is_crypto_target and is_imminent:
                                all_found.append({
                                    "id": m['id'],
                                    "title": m['question'],
                                    "conditionId": m['conditionId'],
                                    "token_yes": tokens[0],
                                    "token_no": tokens[1],
                                    "volume": float(m.get('volume', 0)),
                                    "asset": matched_asset
                                })
                        except: pass
            
            all_found.sort(key=lambda x: x['volume'], reverse=True)
            return all_found[:limit]
            
        except Exception as e:
            log.error(f"Errore Gamma API: {e}")
            return []
