import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENVS = ["PolygonUSDT", "PolygonDGEN", "GnosisXDAI", "ArbitrumUSDT", "BscUSDT"]

def search_global():
    print("=== GLOBAL SEARCH: AZURO V3 SEARCH ENDPOINT ===")
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/"
    }
    
    queries = ["BTC", "ETH", "XRP", "DOGE", "SOL"]
    
    for q in queries:
        print(f"\n🔍 Searching for '{q}'...")
        for env in ENVS:
            url = f"{BASE_URL}/market-manager/search"
            params = {
                "environment": env,
                "request": q,
                "page": 1,
                "perPage": 50
            }
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # L'endpoint search restituisce spesso una struttura con 'games'
                    games = data.get("games", [])
                    if games:
                        print(f"  ✅ [!!!] TROVATI {len(games)} mercati in {env} per {q}:")
                        for g in games:
                            title = g.get('title', 'N/A')
                            print(f"    * {title} (ID: {g.get('gameId')}) | SportID: {g.get('sportId')}")
                else:
                    # print(f"  Error {env}: {resp.status_code}")
                    pass
            except:
                pass

if __name__ == "__main__":
    search_global()
