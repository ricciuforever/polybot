import requests

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENVS = [
    "PolygonUSDT", "PolygonDGEN", "ArbitrumUSDT", "BaseWETH", 
    "LineaUSDT", "GnosisXDAI", "BscUSDT", "ChilizWCHZ"
]

def scan_btc_at_all():
    print(f"--- SCANNING FOR 'BTC' ACROSS ALL ENVS ---")
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/search"
        params = {
            "environment": env,
            "request": "BTC", # 3 caratteri (valida per Azuro Search)
            "page": 1,
            "perPage": 20
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                games = resp.json().get("games", [])
                if games:
                    print(f"\n[!!!] TROVATO in {env}:")
                    for g in games:
                        print(f"  - {g.get('title')} (ID: {g.get('gameId')})")
        except:
            continue

if __name__ == "__main__":
    scan_btc_at_all()
