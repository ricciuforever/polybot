import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def scan_dgen():
    print("=== SCANNING ENVIRONMENT: PolygonDGEN ===")
    url = f"{BASE_URL}/market-manager/games-by-filters"
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/"
    }
    
    # State All non è valido, usiamo Prematch
    params = {
        "environment": "PolygonDGEN",
        "gameState": "Prematch",
        "page": 1,
        "perPage": 100,
        "orderBy": "startsAt",
        "orderDirection": "asc"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            games = resp.json().get('items', [])
            print(f"Trovati {len(games)} giochi in PolygonDGEN")
            for g in games:
                title = g.get('title', 'N/A')
                print(f"  - {title}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
            
        print("\n--- Analisi Live ---")
        params["gameState"] = "Live"
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            games = resp.json().get('items', [])
            print(f"Trovati {len(games)} giochi Live in PolygonDGEN")
            for g in games:
                title = g.get('title', 'N/A')
                print(f"  - {title}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    scan_dgen()
