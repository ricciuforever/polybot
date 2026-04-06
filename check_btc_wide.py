import requests
import json
import config

SUBGRAPH_URL = config.AZURO_SUBGRAPH

query = """
{
  games(where: { title_contains_nocase: "BTC" }, first: 10) {
    id
    gameId
    title
    status
    startsAt
    league { name }
  }
}
"""

def search_btc_no_filter():
    print(f"--- SEARCHING BTC ON {SUBGRAPH_URL} (No status filter) ---")
    try:
        response = requests.post(SUBGRAPH_URL, json={'query': query}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            games = data.get('data', {}).get('games', [])
            if games:
                for g in games:
                    print(f"[{g['status']}] {g['title']} | League: {g['league']['name']} | ID: {g['gameId']}")
            else:
                print("Nessun gioco BTC trovato nemmeno senza filtri.")
        else:
            print(f"Error {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    search_btc_no_filter()
