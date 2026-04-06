import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def brutal_id_scan():
    print("=== BRUTAL ID SCAN: Azuro V3 ===")
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/"
    }
    
    # In Azuro V3, gli sportId dei Prediction Markets sono spesso alti (100+) o specifici.
    url = f"{BASE_URL}/market-manager/games-by-filters"
    
    # State All non è valido, usiamo Prematch e Live
    states = ["Prematch", "Live"]
    for state in states:
        print(f"\n--- SCANNING STATE: {state} ---")
        params = {
            "environment": "PolygonUSDT",
            "gameState": state,
            "page": 1,
            "perPage": 100,
            "orderBy": "startsAt",
            "orderDirection": "desc"
        }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            games = resp.json().get('items', [])
            print(f"Trovati {len(games)} giochi.")
            sports = {}
            for g in games:
                sid = g.get('sportId')
                sname = g.get('sport', {}).get('name')
                title = g.get('title')
                if sid not in sports:
                    sports[sid] = sname
                    print(f"ID Sport Scoperto: {sid} -> {sname}")
                
                if any(x in title.lower() for x in ["bit", "eth", "xrp", "doge", "up", "down"]):
                    print(f"🔥 MATCH: [{sid}] {title}")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    brutal_id_scan()
