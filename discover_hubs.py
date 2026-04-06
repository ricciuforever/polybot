import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def discover_hubs():
    print("=== DISCOVERY SPORTHUBS AZURO V3 ===")
    url = f"{BASE_URL}/market-manager/navigation"
    params = {
        "environment": "PolygonUSDT"
    }
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            nav = resp.json()
            # nav è una dict con chiave 'sports'
            sports = nav.get('sports', [])
            hubs = {}
            for s in sports:
                hub = s.get('sportHub', {})
                hname = hub.get('slug', 'N/A')
                hid = hub.get('id', 'N/A')
                if hname not in hubs:
                    hubs[hname] = hid
                    print(f"Hub Trovato: {hname} (ID: {hid})")
                
                if hname != "sports":
                    print(f"  -> Sport in Hub {hname}: {s.get('name')} (ID: {s.get('sportId')})")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    discover_hubs()
