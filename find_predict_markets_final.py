import requests
import json

# L'unico subgraph che ha restituito dati recenti su Polygon
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

query = """
{
  games(first: 100, where: { title_contains_nocase: "Up" }) {
    id
    gameId
    title
    startsAt
    status
    sport { id name }
    league { id name }
    liquidityPool
  }
}
"""

def find_markets():
    print(f"=== SEARCHING PREDICT MARKETS ON {SUBGRAPH_URL} ===")
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            games = resp.json().get('data', {}).get('games', [])
            if not games:
                print("⚠️ Nessun mercato con 'Up' trovato. Provo broad search...")
                query_all = "{ games(first: 50, orderBy: startsAt, orderDirection: desc) { title sport { name } liquidityPool } }"
                resp = requests.post(SUBGRAPH_URL, json={"query": query_all}, timeout=15)
                games = resp.json().get('data', {}).get('games', [])
            
            if games:
                print(f"✅ Trovati {len(games)} giochi!")
                for g in games:
                    title = g.get('title', 'N/A')
                    lp = g.get('liquidityPool', 'N/A')
                    sport = g.get('sport', {}).get('name', 'N/A')
                    
                    print(f"  - [{sport}] {title}")
                    print(f"    LP: {lp}")
                    
                    if any(kw in title.lower() for kw in ["xrp", "doge", "bit", "eth"]):
                        print("    🎯 [TARGET!] Trovato mercato Crypto.")
            else:
                print("❌ Nessun gioco trovato.")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_markets()
