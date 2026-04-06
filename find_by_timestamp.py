import requests
import json

# Subgraph Data Feed Azuro V3 per le principali reti
SUBGRAPHS = [
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-gnosis",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-arbitrum",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-linea",
]

# Timestamps dagli esempi utente: 1775513100, 1775500500
TIMESTAMPS = [1775513100, 1775500500]

query = """
query($ts: BigInt!) {
  games(where: { startsAt: $ts }) {
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

def find_by_ts():
    print("=== FIND BY TIMESTAMP: AZURO V3 ===")
    for url in SUBGRAPHS:
        print(f"\n🔍 Searching Subgraph: {url}")
        for ts in TIMESTAMPS:
            print(f"  -> Testing startsAt: {ts}")
            try:
                variables = {"ts": str(ts)}
                resp = requests.post(url, json={"query": query, "variables": variables}, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    games = data.get('data', {}).get('games', [])
                    if games:
                        print(f"    ✅ [TROVATI {len(games)} GIOCHI!]")
                        for g in games:
                            print(f"      - {g['title']}")
                            print(f"        SportID: {g['sport']['id']} ({g['sport']['name']})")
                            print(f"        LeagueID: {g['league']['id']} ({g['league']['name']})")
                            print(f"        Azuro ID: {g['gameId']}")
                    else:
                        print("    Nessun match per questo timestamp.")
                else:
                    print(f"    Error {resp.status_code}")
            except Exception as e:
                print(f"    Exception: {e}")

if __name__ == "__main__":
    find_by_ts()
