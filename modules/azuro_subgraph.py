import time
import asyncio
from typing import List, Dict, Any
import aiohttp
import logging
from datetime import datetime

log = logging.getLogger(__name__)

class AzuroMarketsWatcher:
    """Recupera mercati Live (Crypto a 5 Mins) asincronamente dall'API aggregata"""
    def __init__(self, assets: List[str]):
        self.assets = assets

    async def get_imminent_matches(self, limit: int = 20) -> List[Dict[str, Any]]:
        url = "https://dgpredict.com/app/api/markets?limit=100&offset=0&active=true&closed=false&tag_slug=5M&order=volume24hr&ascending=false"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://dgpredict.com/app/crypto"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        log.warning(f"Errore API fetch mercati: {response.status}")
                        return []
                    data = await response.json()
                    
            markets = data.get("markets", [])
            current_time = int(time.time())
            
            valid_markets = []
            for m in markets:
                name = m.get("question", "")
                
                # Extract asset logic
                asset_found = None
                for a in self.assets:
                    if a in name:
                        asset_found = a
                        break
                        
                if not asset_found:
                    continue
                    
                end_time_str = m.get("endTime", "")
                if not end_time_str:
                    continue
                    
                try:
                    # Convert '2026-04-07T18:55:00.000Z' to proper UTC timestamp
                    # Replace Z with +00:00 per python support
                    iso_str = end_time_str.replace('Z', '+00:00')
                    starts_at = int(datetime.fromisoformat(iso_str).timestamp())
                except Exception as e:
                    log.error(f"Date parse error: {e}")
                    continue
                    
                time_diff = starts_at - current_time
                
                # Solo mercati che scadono tra 10 sec e 5 minuti
                if 10 < time_diff < 300:
                    outcomes = m.get("outcomes", [])
                    if outcomes:
                        c_id = outcomes[0].get("conditionId")
                        core = outcomes[0].get("coreAddress")
                        
                        valid_markets.append({
                            "asset": asset_found,
                            "name": name,
                            "conditionId": c_id,
                            "coreAddress": core,
                            "startsAt": starts_at,
                            "outcomes": outcomes,
                            "time_diff": time_diff
                        })
            
            # Sort chronological
            valid_markets.sort(key=lambda x: x["startsAt"])
            
            # Remove duplicates prioritizing nearest
            unique_assets = {}
            for m in valid_markets:
                if m["asset"] not in unique_assets:
                    unique_assets[m["asset"]] = m
                    
            return list(unique_assets.values())
            
        except Exception as e:
            log.error(f"[Markets] Errore di rete: {e}")
            return []
