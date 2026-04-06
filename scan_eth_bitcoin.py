import requests

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
# Proviamo ogni possibile variazione per Ethereum/USDC
ENVS = [
    "Ethereum", "EthereumUSDC", "EthereumUSDT", "EthereumWETH",
    "Gnosis", "GnosisXDAI", "GnosisUSDC", "Polygon", "PolygonUSDC"
]

def scan_ethereum_bitcoin():
    print(f"--- SCANNING ETHEREUM / BITCOIN ---")
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
                games = resp.json().get("games", [])
                if games:
                    print(f"\n[!!!] TROVATO in {env}:")
                    for g in games:
                        print(f"  - {g.get('title')} (ID: {g.get('gameId')})")
        except:
            continue

if __name__ == "__main__":
    scan_ethereum_bitcoin()
