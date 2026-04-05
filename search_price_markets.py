import requests
import json

# Proviamo entrambi gli host possibili per Azuro V3 Polygon
ENDPOINTS = [
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3",
    "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
]

query = """
{
  games(where: { status: Created, title_contains: "Price" }) {
    id
    gameId
    title
    sport { name }
    conditions {
      conditionId
      outcomes {
        outcomeId
      }
    }
  }
}
"""

def search():
    for url in ENDPOINTS:
        print(f"Testing {url}...")
        try:
            response = requests.post(url, json={'query': query}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                games = data.get('data', {}).get('games', [])
                if games:
                    print(f"Trovati {len(games)} mercati 'Price':")
                    print(json.dumps(games, indent=2))
                    return
                else:
                    print("Nessun mercato 'Price' trovato.")
            else:
                print(f"Status {response.status_code}")
        except Exception as e:
            print(f"Errore: {e}")

if __name__ == "__main__":
    search()
