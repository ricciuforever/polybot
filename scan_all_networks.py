import requests
import json

SUBGRAPHS = {
    "Polygon": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon",
    "Gnosis": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-gnosis",
    "Arbitrum": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-arbitrum",
    "Linea": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-linea",
    "Base": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-base",
}

query = """
{
  games(first: 100, where: { status: Created }) {
    id
    gameId
    title
    startsAt
    sport { id name }
    league { id name }
  }
}
"""

def scan_all():
    print("=== UNIVERSAL CRYPTO SCAN: Azuro V3 ===")
    keywords = ["bitcoin", "eth", "xrp", "doge", "sol", "up", "down"]
    
    for name, url in SUBGRAPHS.items():
        print(f"\n📡 Scansione catena: {name} ({url})...")
        try:
            resp = requests.post(url, json={"query": query}, timeout=15)
            if resp.status_code == 200:
                games = resp.json().get('data', {}).get('games', [])
                found_count = 0
                for g in games:
                    title = g.get('title', '').lower()
                    if any(kw in title for kw in keywords):
                        print(f"  🎯 [MATCH!] {g['title']}")
                        print(f"     -> GameID: {g['gameId']} | SportID: {g['sport']['id']} ({g['sport']['name']})")
                        print(f"     -> LeagueID: {g['league']['id']} ({g['league']['name']})")
                        found_count += 1
                
                if found_count == 0:
                    print(f"  (Nessun mercato crypto trovato tra i primi 100 in {name})")
            else:
                print(f"  ❌ Errore HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ⚠ Eccezione: {e}")

if __name__ == "__main__":
    scan_all()
