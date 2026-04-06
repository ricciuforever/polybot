import requests

NEW_BASE_URL = "https://api.azuro.org/api/v1/public"
ENV = "PolygonUSDT"

def test_new_api():
    url = f"{NEW_BASE_URL}/market-manager/search"
    params = {
        "environment": ENV,
        "request": "Bitcoin",
        "page": 1,
        "perPage": 10
    }
    print(f"Testing {url}...")
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Trovati {len(resp.json().get('games', []))} giochi.")
        else:
            print(f"Errore: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_new_api()
