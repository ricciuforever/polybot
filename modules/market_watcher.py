"""
modules/market_watcher.py — Trova i mercati Up/Down 5 minuti correnti per gli asset supportati.
"""
import json
import time
import requests
import config
from modules.logger import get_logger

log = get_logger("market_watcher")

GAMMA_EVENTS = f"{config.GAMMA_URL}/events"
CLOB_BOOK    = f"{config.CLOB_URL}/book"

def _current_bucket() -> int:
    return (int(time.time()) // 300) * 300

class MarketWatcher:

    def find_market(self, asset: str) -> dict | None:
        """Cerca il mercato 5m corrente per un asset specifico (es. 'BTC', 'ETH')."""
        bucket = _current_bucket()
        slug_prefix = f"{asset.lower()}-updown-5m"
        
        for offset in [0, -300]:
            slug = f"{slug_prefix}-{bucket + offset}"
            market = self._fetch_by_slug(slug)
            if market: 
                market["asset"] = asset
                return market
        return None

    def _fetch_by_slug(self, slug: str) -> dict | None:
        try:
            resp = requests.get(GAMMA_EVENTS, params={"slug": slug}, timeout=8)
            events = resp.json()
            if not events or not isinstance(events, list): return None
            
            event = events[0]
            m = event.get("markets", [{}])[0]
            clob_ids = json.loads(m.get("clobTokenIds", "[]")) if isinstance(m.get("clobTokenIds"), str) else m.get("clobTokenIds")
            outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes"), str) else m.get("outcomes")
            prices   = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices")

            if not clob_ids or len(clob_ids) < 2: return None
            
            up_idx = next((i for i, o in enumerate(outcomes or []) if "up" in str(o).lower()), 0)
            down_idx = 1 - up_idx

            return {
                "title": event.get("question", slug),
                "slug": slug,
                "bucket": (int(slug.split('-')[-1])),
                "up_token": clob_ids[up_idx],
                "down_token": clob_ids[down_idx],
                "up_price": float(prices[up_idx]) if prices else 0.5,
                "down_price": float(prices[down_idx]) if prices else 0.5,
                "conditionId": m.get("conditionId")
            }
        except Exception: return None

    def get_prices(self, market: dict) -> tuple[float, float]:
        """Recupera odds reali (Gamma API fallback prioritario)."""
        try:
            slug = market.get("slug")
            resp = requests.get(GAMMA_EVENTS, params={"slug": slug}, timeout=5)
            data = resp.json()
            if data and "markets" in data[0]:
                m = data[0]["markets"][0]
                prices = m.get("outcomePrices")
                if prices:
                    outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes"), str) else m.get("outcomes")
                    up_idx = next((i for i, o in enumerate(outcomes or []) if "up" in str(o).lower()), 0)
                    down_idx = 1 - up_idx
                    return float(prices[up_idx]), float(prices[down_idx])
        except Exception: pass
        return market.get("up_price", 0.5), market.get("down_price", 0.5)

    def get_token_ids(self, market: dict) -> tuple[str, str]:
        return market.get("up_token"), market.get("down_token")
