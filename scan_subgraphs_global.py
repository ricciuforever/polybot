import requests
import json
import time

SUBGRAPHS = {
    "PolygonV3": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3",
    "ArbitrumV3": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-arbitrum-v3",
    "GnosisV3": "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-gnosis-v3",
    "ChilizV3": "https://api.goldsky.com/api/public/project_clv1vqz96996p01x949987l7a/subgraphs/azuro-api-chiliz-v3/latest/gn"
}

query_template = """
{
  games(where: { title_contains_nocase: "BTC", startsAt_gt: %d }, first: 5) {
    id
    gameId
    title
    startsAt
    league { name }
  }
}
"""

def scan_all_subgraphs():
    print(f"--- AZURO MULTI-SUBGRAPH SCAN (BTC) ---")
    current_time = int(time.time())
    for name, url in SUBGRAPHS.items():
        print(f"\nScanning {name}...")
        try:
            current_query = """
            {
              games(where: { title_contains_nocase: "BTC" }, first: 10, orderBy: startsAt, orderDirection: desc) {
                gameId
                title
                startsAt
                league { name }
              }
            }
            """
            response = requests.post(url, json={'query': current_query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                games = data.get('data', {}).get('games', [])
                if games:
                    print(f"  [SUCCESS] Found {len(games)} games:")
                    for g in games:
                        print(f"    - {g['title']} (League: {g['league']['name']} | Starts: {g['startsAt']})")
                else:
                    print("  [INFO] No BTC games found.")
            else:
                print(f"  [ERROR] Status {response.status_code}")
        except Exception as e:
            print(f"  [EXCEPTION] {str(e)}")

if __name__ == "__main__":
    scan_all_subgraphs()
