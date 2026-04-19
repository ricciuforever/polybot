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
        """Trova i mercati crypto attivi"""
        import time
        from datetime import datetime, timezone
        
        now_ts = int(time.time())
        rounded_down = (now_ts // 300) * 300
        
        all_found = []
        # Verifichiamo sia il bucket attuale che il prossimo per coprire i cambi di ciclo
        buckets_to_check = [rounded_down, rounded_down + 300]
        
        for asset in self.crypto_keywords.keys():
            for bucket_ts in buckets_to_check:
                slug = f"{asset.lower()}-updown-5m-{bucket_ts}"
                endpoint = f"{self.url}/events"
                params = {"slug": slug}
                
                try:
                    resp = requests.get(endpoint, params=params, timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            e = data[0]
                            markets = e.get("markets", [])
                            for m in markets:
                                q = m.get('question', '').lower()
                                if 'up or down' in q:
                                    clob_ids = m.get('clobTokenIds')
                                    if clob_ids:
                                        tokens = json.loads(clob_ids)
                                        start_dt_str = e.get('eventStartTime') or m.get('startDate')
                                        end_dt_str = m.get('endDate')
                                        
                                        try:
                                            start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00')).timestamp() if start_dt_str else float(bucket_ts)
                                            end_dt = datetime.fromisoformat(end_dt_str.replace('Z', '+00:00')).timestamp() if end_dt_str else float(bucket_ts + 300)
                                        except Exception:
                                            start_dt = float(bucket_ts)
                                            end_dt = float(bucket_ts + 300)
                                            
                                        diff_sec = end_dt - time.time()
                                        
                                        if 0 < diff_sec <= 420:
                                            all_found.append({
                                                "id": m['id'],
                                                "slug": m.get('slug'),
                                                "title": m['question'],
                                                "conditionId": m['conditionId'],
                                                "token_yes": tokens[0],
                                                "token_no": tokens[1],
                                                "volume": float(m.get('volume', 0)),
                                                "asset": asset,
                                                "start_timestamp": start_dt,
                                                "end_timestamp": end_dt
                                            })
                except Exception as e:
                    log.error(f"Errore scansione bucket {slug}: {e}")

        # Ordiniamo dal più imminente in poi (quello currently live)
        all_found.sort(key=lambda x: x['end_timestamp'])
        
        # Restituiamo il PIU' imminente PER OGNI ASSET limitato all'asset richiesto (o tutti)
        asset_best = {}
        for m in all_found:
            if m['asset'] not in asset_best:
                asset_best[m['asset']] = m
                
        return list(asset_best.values())
