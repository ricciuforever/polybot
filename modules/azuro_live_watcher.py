import aiohttp
import logging
import json
from typing import List, Dict, Any
import config

log = logging.getLogger("azuro_live_watcher")

class AzuroLiveWatcher:
    """Monitora match Live Sportivi direttamente dal Data-Feed Subgraph di Azuro V3."""
    
    def __init__(self):
        self.url = config.AZURO_DATA_FEED_URL

    async def get_live_games(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Recupera i match LIVE dal Subgraph (Unfiltered)."""
        query = """
        query GetLiveGames($limit: Int!) {
          games(
            where: { isLive: true, liquidity_gt: 0 }, 
            first: $limit, 
            orderBy: turnover, 
            orderDirection: desc
          ) {
            gameId
            title
            sport { name }
            league { name }
            turnover
            conditions(where: { status: Created }) {
              conditionId
              outcomes {
                outcomeId
                odds
              }
            }
          }
        }
        """
        variables = {"limit": limit}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json={'query': query, 'variables': variables}, timeout=10) as response:
                    if response.status != 200:
                        log.warning(f"Errore Subgraph Data-Feed: {response.status}")
                        return []
                    
                    data = await response.json()
                    games_data = data.get('data', {}).get('games', [])
                    
                    processed_games = []
                    for g in games_data:
                        # Filtro Sport (No Crypto)
                        sport_name = g.get('sport', {}).get('name', '')
                        if "Crypto" in sport_name: continue
                        
                        # Cerchiamo la condizione principale (es. 1X2 o Winner)
                        if not g.get('conditions'): continue
                        
                        main_cond = g['conditions'][0]
                        
                        processed_games.append({
                            "gameId": g['gameId'],
                            "title": g['title'],
                            "sport": sport_name,
                            "league": g.get('league', {}).get('name', ''),
                            "turnover": float(g.get('turnover', 0)),
                            "conditionId": main_cond['conditionId'],
                            "outcomes": [
                                {"outcomeId": o['outcomeId'], "odds": float(o['odds'])} 
                                for o in main_cond['outcomes']
                            ]
                        })
                    
                    log.info(f"📡 Subgraph Feed: {len(processed_games)} match live sportivi trovati.")
                    return processed_games
                    
        except Exception as e:
            log.error(f"Errore query Subgraph Data-Feed: {e}")
            return []

if __name__ == "__main__":
    import asyncio
    async def test():
        watcher = AzuroLiveWatcher()
        games = await watcher.get_live_games()
        for g in games:
            print(f"Match: {g['title']} | Sport: {g['sport']} | Cond: {g['conditionId']}")
    
    asyncio.run(test())
