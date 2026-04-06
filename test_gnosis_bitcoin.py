import requests

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENV = "GnosisXDAI"

def scan_gnosis_bitcoin():
    url = f"{BASE_URL}/market-manager/search"
    params = {
        "environment": ENV,
        "request": "Bitcoin",
        "page": 1,
        "perPage": 20
    }
    print(f"Testing environment: {ENV}")
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            games = resp.json().get("games", [])
            print(f"Trovati {len(games)} mercati Bitcoin su Gnosis.")
            for g in games:
                print(f"  - {g.get('title')} (ID: {g.get('gameId')})")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    scan_gnosis_bitcoin()
