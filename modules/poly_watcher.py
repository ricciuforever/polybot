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
        endpoint = f"{self.url}/events"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 500
        }
        
        all_found = []
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            if resp.status_code != 200:
                log.error(f"Errore Gamma API: {resp.status_code}")
                return []
            
            events = resp.json()
            data = []
            for e in events:
                if e.get("markets"):
                    data.extend(e["markets"])
                    
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
                    clob_ids = m.get('clobTokenIds')
                    end_date_str = m.get('endDate')
                    start_date_str = m.get('eventStartTime') or m.get('startDate')
                    
                    if clob_ids and end_date_str and start_date_str:
                        try:
                            from datetime import datetime, timezone
                            end_dt = datetime.strptime(end_date_str.replace('Z', '+0000'), "%Y-%m-%dT%H:%M:%S%z")
                            start_dt = datetime.strptime(start_date_str.replace('Z', '+0000'), "%Y-%m-%dT%H:%M:%S%z")
                            now_dt = datetime.now(timezone.utc)
                            
                            # Filtro: solo il mercato che scade entro i prossimi 0-7 minuti
                            diff_sec = (end_dt - now_dt).total_seconds()
                            if 0 < diff_sec <= 420:
                                tokens = json.loads(clob_ids)
                                is_crypto_target = any(x in q for x in ["up or down"])
                                
                                if is_crypto_target:
                                    all_found.append({
                                        "id": m['id'],
                                        "slug": m.get('slug'),
                                        "title": m['question'],
                                        "conditionId": m['conditionId'],
                                        "token_yes": tokens[0],
                                        "token_no": tokens[1],
                                        "volume": float(m.get('volume', 0)),
                                        "asset": matched_asset,
                                        "start_timestamp": start_dt.timestamp(),
                                        "end_timestamp": end_dt.timestamp()
                                    })
                        except Exception as e: 
                            pass
            
            # Ordiniamo dal più imminente in poi (quello currently live)
            all_found.sort(key=lambda x: x['end_timestamp'])
            return all_found[:1]
            
        except Exception as e:
            log.error(f"Errore Gamma API: {e}")
            return []
