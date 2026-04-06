import requests

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
# Proviamo a cercare tra i provider specifici. 
# Provider ID comuni in Azuro: 1 (Sport), 2 (Crypto/Novelty?)
ENVS = ["PolygonUSDT", "GnosisXDAI", "ArbitrumUSDT"]

def scan_provider_games():
    print(f"--- SCANNING PROVIDER GAMES ---")
    for env in ENVS:
        # Proviamo providerId da 1 a 10
        for pid in range(1, 11):
            url = f"{BASE_URL}/market-manager/provider-games"
            params = {
                "environment": env,
                "providerId": pid,
                "page": 1,
                "perPage": 20
            }
            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    games = resp.json().get("games", [])
                    if games:
                        print(f"\n[!!!] TROVATO in {env} (Provider {pid}):")
                        for g in games:
                            print(f"  - {g.get('title')}")
            except:
                continue

if __name__ == "__main__":
    scan_provider_games()
