import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"

query = """
{
  games(first: 50, orderBy: startsAt, orderDirection: desc, where: { sport_: { id: "100" } }) {
    id
    gameId
    title
    startsAt
    status
    sport { id name }
    league { id name }
  }
}
"""

def find_sport_100():
    print("=== SEARCH SPORT 100: AZURO V3 (Polygon) ===")
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            games = resp.json().get('data', {}).get('games', [])
            if games:
                print(f"✅ TROVATI {len(games)} GIOCHI in Sport 100!")
                for g in games[:10]:
                    print(f"  - {g['title']} (Starts: {g['startsAt']}) | ID: {g['gameId']}")
            else:
                print("Nessun gioco trovato per Sport 100.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_sport_100()
