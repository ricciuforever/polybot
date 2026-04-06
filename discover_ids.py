import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def discover():
    print("=== DISCOVERY AZURO V3: IDENTIFICAZIONE ID CATEGORIE ===")
    
    # Tentiamo di recuperare gli sport
    # In V3, molti endpoint richiedono chainId
    endpoints = [
        "/market-manager/sports",
        "/market-manager/navigation"
    ]
    
    for ep in endpoints:
        print(f"\n--- Testing {ep} ---")
        for cid in [137, 80001, 80002]: # Polygon, Mumbai, Amoy
            params = {"chainId": cid}
            try:
                url = f"{BASE_URL}{ep}"
                resp = requests.get(url, params=params, timeout=10)
                print(f"Chain {cid}: Status {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    # Se è navigation, esploriamo
                    if ep == "/market-manager/navigation":
                        for sport in data:
                            print(f"  Sport: {sport.get('name')} (ID: {sport.get('sportId')})")
                            for country in sport.get('countries', []):
                                for league in country.get('leagues', []):
                                    lname = league.get('name')
                                    if any(x in lname.lower() for x in ["bit", "cry"]):
                                        print(f"    [!] TROVATO: {lname} | leagueId: {league.get('leagueId')} (Sport ID: {sport.get('sportId')})")
                    # Se è sports, stampiamo tutti
                    else:
                        for s in data:
                            print(f"  - {s.get('name')} (ID: {s.get('sportId')})")
            except Exception as e:
                print(f"  Errore su {cid}: {e}")

if __name__ == "__main__":
    discover()
