import requests
import json

# Endpoint Azure V3 API
DATA_FEED_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

query = """
{
  leagues(first: 100) {
    id
    name
  }
}
"""

def fetch_azuro_btc_conditions():
    try:
        response = requests.post(DATA_FEED_URL, json={'query': query}, timeout=15)
        if response.status_code != 200:
            print(f"Errore HTTP {response.status_code}: {response.text}")
            return
            
        data = response.json()
        if 'errors' in data:
            print("Errori GraphQL:")
            print(json.dumps(data['errors'], indent=2))
            return
            
        games = data.get('data', {}).get('games', [])
        if not games:
            print("Nessun mercato BTC attivo trovato.")
            return

        print(f"Trovati {len(games)} giochi BTC:")
        for g in games:
            print(f"\n--- {g['title']} (ID: {g['gameId']}) ---")
            for c in g.get('conditions', []):
                print(f"  Condition ID: {c['conditionId']} | Status: {c['status']}")
                for o in c.get('outcomes', []):
                    # Odds sono in formato ray o decimal? Azuro usa ray (10^12) o float?
                    # Nel subgraph di solito sono float o stringhe float
                    print(f"    Outcome {o['outcomeId']}: Odds {o['currentOdds']}")
                    
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    fetch_azuro_btc_conditions()
