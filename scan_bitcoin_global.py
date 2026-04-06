import requests

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
# Proviamo tutti gli env possibili inclusi quelli suggeriti
ENVS = [
    "PolygonUSDT", "PolygonDGEN", "ArbitrumUSDT", "BaseWETH", 
    "LineaUSDT", "GnosisXDAI", "BscUSDT", "EthereumUSDC", "EthereumUSDT"
]

def scan_bitcoin_everywhere():
    print(f"--- BITCOIN SEARCH ACROSS ALL ENVS ---")
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/search"
        params = {
            "environment": env,
            "request": "Bitcoin", # Stringa di 7 caratteri (valida)
            "page": 1,
            "perPage": 20
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                games = data.get("games", [])
                if games:
                    print(f"\n[!!!] TROVATO in {env} ({len(games)} giochi):")
                    for g in games:
                        print(f"  - {g.get('title')} (ID: {g.get('gameId')})")
            else:
                # Se l'env non esiste, darà 400 o 404
                if resp.status_code != 400:
                    print(f"[{env}] Status {resp.status_code}")
        except:
            continue

if __name__ == "__main__":
    scan_bitcoin_everywhere()
