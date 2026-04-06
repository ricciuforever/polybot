import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
# Testiamo lo slug specifico in tutti gli env di Polygon
SLUG = "btc-updown-5m-1775480400"
ENVS = ["PolygonUSDT", "PolygonDGEN", "ArbitrumUSDT", "GnosisXDAI"]

def test_slug():
    print(f"--- TESTING SLUG: {SLUG} ---")
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/game/{SLUG}" # Assumendo /game/{slug} o simile
        params = {"environment": env}
        print(f"\nTesting {env}...")
        try:
            resp = requests.get(url, params=params, timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(json.dumps(resp.json(), indent=2))
                return
        except:
            continue
    print("Fine test slug.")

if __name__ == "__main__":
    test_slug()
