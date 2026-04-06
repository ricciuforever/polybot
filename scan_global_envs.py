import requests
import json
import time

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENVS = [
    "PolygonUSDT",
    "PolygonDGEN",
    "ArbitrumUSDT",
    "BaseWETH",
    "LineaUSDT",
    "GnosisXDAI"
]

def scan_all_envs():
    print(f"--- GLOBAL SCANNER (Bitcoin/Crypto) ---")
    
    for env in ENVS:
        url = f"{BASE_URL}/market-manager/navigation"
        print(f"\nScanning Navigation for {env}...")
        try:
            resp = requests.get(url, params={"environment": env}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for sport in data:
                    s_name = sport.get('name', '')
                    if "Crypto" in s_name or "Bitcoin" in s_name or "Financial" in s_name:
                        print(f"  [!!!] SPORT TROVATO in {env}: {s_name} (ID: {sport.get('sportId')})")
                    
                    # Scansione League
                    for country in sport.get('countries', []):
                        for league in country.get('leagues', []):
                            L_name = league.get('name', '')
                            if "Bitcoin" in L_name or "Crypto" in L_name or "Up" in L_name:
                                print(f"    [!!!] LEAGUE TROVATA in {env}: {L_name} (ID: {league.get('id')})")
            else:
                print(f"  Error {resp.status_code}")
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    scan_all_envs()
