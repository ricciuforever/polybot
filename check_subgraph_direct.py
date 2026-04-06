import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"

query = """
{
  games(first: 50, where: { sport: "100" }) {
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
# Nota: in GraphQL Azuro, sport potrebbe essere un ID stringa o un oggetto. 
# Se 'sport' è un oggetto, la query corretta è where: { sport_: { id: "100" } }

def search_subgraph():
    print("=== SUBGRAPH SEARCH: Azuro V3 Prediction Markets ===")
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            games = data.get('data', {}).get('games', [])
            if not games:
                print("Nessun mercato con 'Up' nel titolo trovato nel Subgraph.")
                # Tentativo broad
                print("Provo ultimi 20 giochi generici...")
                query_broad = "{ games(first: 20, orderBy: startsAt, orderDirection: desc) { title sport { name } } }"
                resp2 = requests.post(SUBGRAPH_URL, json={"query": query_broad}, timeout=15)
                for g in resp2.json().get('data', {}).get('games', []):
                    print(f"  - {g['title']} ({g['sport']['name'] if g['sport'] else 'N/A'})")
            else:
                for g in games:
                    print(f"🎯 [{g['status']}] {g['title']} | Sport: {g['sport']['name']} (ID: {g['sport']['id']})")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    search_subgraph()
