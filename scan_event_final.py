import requests

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
# Proviamo TUTTI gli environment Azuro V3 conosciuti
ENVS = [
    "PolygonUSDT", "PolygonDGEN", "ArbitrumUSDT", "BaseWETH", 
    "LineaUSDT", "GnosisXDAI", "BscUSDT", "EthereumUSDT", "ChilizWCHZ"
]

def scan_event_id():
    print(f"--- SCANNING FOR 'btc-updown' / '1775480400' ---")
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/search"
        # Usiamo il termine dell'URL: "Bitcoin Up or Down" o "btc-updown"
        for term in ["Bitcoin", "Up or Down", "btc-updown"]:
            params = {
                "environment": env,
                "request": term,
                "page": 1,
                "perPage": 20
            }
            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    games = resp.json().get("games", [])
                    if games:
                        print(f"\n[!!!] TROVATO in {env} con termine '{term}':")
                        for g in games:
                            print(f"  - Title: {g.get('title')} | ID: {g.get('gameId')}")
            except:
                continue

if __name__ == "__main__":
    scan_event_id()
