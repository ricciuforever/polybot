import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

query = """
{
  games(first: 50, orderBy: startsAt, orderDirection: desc) {
    id
    gameId
    title
    startsAt
    league { name }
    sport { name }
  }
}
"""

def fetch_latest_games():
    print(f"--- FETCHING LATEST 50 GAMES ON POLYGON V3 ---")
    try:
        response = requests.post(SUBGRAPH_URL, json={'query': query}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            games = data.get('data', {}).get('games', [])
            for g in games:
                print(f"[{g['startsAt']}] {g['title']} | League: {g['league']['name']} | Sport: {g['sport']['name']} | ID: {g['gameId']}")
        else:
            print(f"Error {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    fetch_latest_games()
