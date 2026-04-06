import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENV = "PolygonUSDT"

def find_bitcoin_in_nav():
    url = f"{BASE_URL}/market-manager/navigation"
    params = {"environment": ENV}
    print(f"Ispesionando Navigation per {ENV}...")
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            nav_data = resp.json()
            # Cerchiamo Bitcoin o Crypto ricorsivamente
            def search_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, (dict, list)):
                            search_recursive(v, f"{path}.{k}" if path else k)
                        elif isinstance(v, str) and ("Bitcoin" in v or "Crypto" in v):
                            print(f"[FOUND] '{v}' at path: {path}.{k}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_recursive(item, f"{path}[{i}]")

            search_recursive(nav_data)
            print("Fine scansione.")
        else:
            print(f"Errore: {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_bitcoin_in_nav()
