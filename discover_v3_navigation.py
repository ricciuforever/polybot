import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def discover_nav():
    print("=== DISCOVERY NAV V3 ===")
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
            
            for sport in sports:
                s_name = sport.get('name', '')
                s_id = sport.get('sportId')
                
                # Check sport name
                if any(kw in s_name.lower() for kw in ["crypto", "predict", "bitcoin", "finance", "price"]):
                    print(f"🎯 TROVATO SPORT: {s_name} (ID: {s_id})")
                
                # Check leagues
                for country in sport.get('countries', []):
                    for league in country.get('leagues', []):
                        l_name = league.get('name', '')
                        if any(kw in l_name.lower() for kw in ["bit", "eth", "doge", "xrp", "sol", "price", "up", "predict"]):
                            print(f"   🚀 TROVATA LEAGUE: {l_name} (ID: {league.get('id')}) | Sport: {s_name} ({s_id})")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    discover_nav()
