import requests
import json
import time

# Host configurabili
ENDPOINTS = [
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3",
    "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"
]

query = """
{
  games(first: 50, where: { status_in: [Created, Resolved] }) {
    id
    gameId
    title
    startsAt
    sport { name }
    conditions {
      conditionId
      status
      outcomes {
        outcomeId
        currentOdds
      }
    }
  }
}
"""

def fetch_all_active_azuro():
    for url in ENDPOINTS:
        print(f"\nTentativo su {url}...")
        try:
            response = requests.post(url, json={'query': query}, timeout=15)
            if response.status_code != 200:
                print(f"HTTP {response.status_code}")
                continue
                
            data = response.json()
            if 'errors' in data:
                print(f"Errori GraphQL: {data['errors'][0]['message']}")
                continue
                
            games = data.get('data', {}).get('games', [])
            if not games:
                print("Nessun gioco trovato in generale.")
                continue

            found_btc = False
            for g in games:
                title = g['title'].lower()
                if "btc" in title or "bitcoin" in title or "crypto" in title:
                    found_btc = True
                    print(f"\n[TROVATO] {g['title']} (Game ID: {g['gameId']})")
                    print(f"  Sport: {g['sport']['name'] if g['sport'] else 'N/A'}")
                    for c in g.get('conditions', []):
                        print(f"  Condition ID: {c['conditionId']} (Status: {c['status']})")
                        for o in c.get('outcomes', []):
                            print(f"    Outcome {o['outcomeId']}: Odds {o['currentOdds']}")

            if not found_btc:
                print("L'endpoint risponde ma nessun gioco contiene 'BTC' o 'Bitcoin' nei primi 50.")
                # Stampo i primi 3 per vedere cosa c'è
                for g in games[:3]:
                    print(f"--- Esempio Gioco: {g['title']} ({g['sport']['name'] if g['sport'] else 'N/A'})")

        except Exception as e:
            print(f"Errore: {e}")

if __name__ == "__main__":
    fetch_all_active_azuro()
