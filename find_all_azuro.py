import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def scan_all():
    envs = ["PolygonUSDT", "GnosisXDAI", "ArbitrumUSDT", "LineaUSDT", "BscUSDT"]
    states = ["Created", "Prematch", "Live", "Resolved"]
    
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
    }

    for env in envs:
        print(f"\n>>> TESTING ENV: {env}")
        for state in states:
            url = f"{BASE_URL}/market-manager/games-by-filters"
            params = {
                "environment": env,
                "gameState": state,
                "page": 1,
                "perPage": 100
            }
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    games = resp.json().get('items', [])
                    if games:
                        print(f"  - [{state}] Trovati {len(games)} giochi.")
                        for g in games[:5]: # Mostra solo i primi 5 per brevità
                            print(f"    * {g.get('title')}")
            except Exception as e:
                # print(f"Error {env} {state}: {e}")
                pass

if __name__ == "__main__":
    scan_all()
