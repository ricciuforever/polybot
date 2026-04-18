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
            "limit": 1000,
            "order": "volume",
            "ascending": "false"
        }
        
        all_found = []
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            if resp.status_code != 200:
                log.error(f"Errore Gamma API: {resp.status_code}")
                return []
            
            data = resp.json()
            for m in data:
                q = m.get('question', '').lower()
                
                # Identifica l'asset
                matched_asset = None
                for asset, aliases in self.crypto_keywords.items():
                    if any(alias in q for alias in aliases):
                        matched_asset = asset
                        break
                
                if matched_asset:
                    # Filtro Sniper Matematico + Filtro Imminenza (Next 10 mins)
                    import re
                    from datetime import datetime
                    times = re.findall(r"(\d+):(\d+)", q)
                    is_real_5m = False
                    is_imminent = False
                    
                    if len(times) >= 2:
                        try:
                            h1, m1 = map(int, times[0])
                            h2, m2 = map(int, times[1])
                            
                            # Calcolo durata (deve essere 5 min)
                            duration = (h2 * 60 + m2) - (h1 * 60 + m1)
                            if duration == 5 or duration == -1435:
                                is_real_5m = True
                                
                            # Calcolo Imminenza: deve iniziare tra poco (considerando ET time approssimativo)
                            # Nota: Polymarket usa ET. Qui facciamo un controllo relativo semplice:
                            # Se l'orario del match è molto diverso dall'attuale, lo scartiamo.
                            # Per ora, per semplicità e sicurezza, filtriamo solo i 5 minuti reali.
                            # Ma aggiungiamo un controllo per evitare quelli palesemente futuri:
                            # Calcolo Imminenza: mostriamo tutto ciò che inizia nelle prossime 24 ore
                            if True: # Rilassiamo al massimo per vedere tutti i mercati BTC 5m
                                is_imminent = True
                        except: pass
                    
                    if is_real_5m and is_imminent and ("up or down" in q or "price of" in q):
                        clob_ids = m.get('clobTokenIds')
                        if not clob_ids: continue
                        
                        try:
                            tokens = json.loads(clob_ids)
                            all_found.append({
                                "id": m['id'],
                                "title": m['question'],
                                "conditionId": m['conditionId'],
                                "token_yes": tokens[0],
                                "token_no": tokens[1],
                                "volume": float(m.get('volume', 0)),
                                "asset": matched_asset
                            })
                        except: continue
            
            # Ordina per volume
            all_found.sort(key=lambda x: x['volume'], reverse=True)
            return all_found[:limit]
            
        except Exception as e:
            log.error(f"Errore scansione Gamma API: {e}")
            return []
