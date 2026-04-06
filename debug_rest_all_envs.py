import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENVS = [
    "PolygonUSDT",
    "PolygonDGEN",
    "PolygonAmoyUSDT",
    "PolygonAmoyAZUSD",
    "PolygonAmoyDGEN",
    "PolygonMumbaiUSDT"
]

def debug_envs():
    print(f"--- AZURO ENVS SCANNER (Bitcoin) ---")
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/search"
        params = {
            "environment": env,
            "request": "Bitcoin",
            "page": 1,
            "perPage": 10
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                games = data.get("games", [])
                print(f"[{env}] Trovati {len(games)} giochi.")
                for g in games:
                    print(f"  - {g.get('title')} (State: {g.get('state')})")
            else:
                print(f"[{env}] Error {resp.status_code}")
        except:
            print(f"[{env}] Timeout/Error")

    print(f"\n--- AZURO ENVS SCANNER (Price) ---")
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/search"
        params = {
            "environment": env,
            "request": "Price",
            "page": 1,
            "perPage": 10
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                games = data.get("games", [])
                print(f"[{env}] Trovati {len(games)} giochi.")
                for g in games:
                    print(f"  - {g.get('title')} (State: {g.get('state')})")
        except:
            continue

if __name__ == "__main__":
    debug_envs()
