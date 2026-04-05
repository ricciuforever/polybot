import requests
import config
import time
from modules.logger import get_logger

log = get_logger("azuro_watcher")

class AzuroWatcher:
    def __init__(self):
        # Endpoint V3 configurato in config.py
        self.url = config.AZURO_SUBGRAPH

    def find_btc_market(self):
        """
        Cerca il mercato BTC attivo più vicino tramite i Game.
        """
        query = """
        {
          games(
            where: { 
              status: Created,
              OR: [
                { title_contains: "Bitcoin" },
                { title_contains: "BTC" },
                { sport_: { name_contains: "Crypto" } }
              ]
            },
            first: 5,
            orderBy: startsAt,
            orderDirection: asc
          ) {
            id
            title
            startsAt
            conditions {
              conditionId
              status
              coreAddress
              outcomes {
                outcomeId
                currentOdds
              }
            }
          }
        }
        """
        try:
            resp = requests.post(self.url, json={'query': query}, timeout=10)
            if resp.status_code != 200:
                log.error(f"Errore Subgraph HTTP {resp.status_code}")
                return None
                
            games = resp.json().get('data', {}).get('games', [])
            if not games:
                log.warning("Nessun gioco BTC trovato su Azuro.")
                return None
            
            now = int(time.time())
            for g in games:
                starts_at = int(g['startsAt'])
                # Consideriamo giochi che inizieranno o sono appena iniziati
                if starts_at > now - 300:
                    for c in g.get('conditions', []):
                        # Se abbiamo un core configurato, filtriamo per quello
                        if hasattr(config, "AZURO_CORE") and c['coreAddress'].lower() != config.AZURO_CORE.lower():
                            continue
                        
                        if c['status'] == 'Created':
                            log.info(f"Mercato rilevato: {g['title']} | Inizio: {time.ctime(starts_at)}")
                            outcomes = {o['outcomeId']: float(o['currentOdds']) for o in c['outcomes']}
                            return {
                                "conditionId": c['conditionId'],
                                "title": g['title'],
                                "startsAt": starts_at,
                                "outcomes": outcomes
                            }
            return None
        except Exception as e:
            log.error(f"Errore nel watcher Azuro: {e}")
            return None

if __name__ == "__main__":
    # Test veloce
    from dotenv import load_dotenv
    load_dotenv()
    watcher = AzuroWatcher()
    market = watcher.find_btc_market()
    if market:
        print(f"\n[OK] Mercato trovato!")
        print(f"Titolo: {market['title']}")
        print(f"Condition ID: {market['conditionId']}")
        print(f"Outcomes: {market['outcomes']}")
    else:
        print("\n[!] Nessun mercato trovato.")
