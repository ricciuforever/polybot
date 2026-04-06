import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def deep_scan():
    print("=== DEEP SCAN AZURO V3: DGPredict Headers ===")
    
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    envs = ["PolygonUSDT", "PolygonDGEN", "GnosisXDAI"]
    states = ["Created", "Prematch", "Live", "Resolved"]

    found_any = False

    for env in envs:
        for state in states:
            print(f"\n🔍 Analisi {env} - {state}...")
            url = f"{BASE_URL}/market-manager/games-by-filters"
            params = {
                "environment": env,
                "gameState": state,
                "page": 1,
                "perPage": 100,
                "orderBy": "startsAt",
                "orderDirection": "asc"
            }
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    games = data.get('items', [])
                    if games:
                        print(f"  ✅ Trovati {len(games)} giochi!")
                        for g in games:
                            title = g.get('title', 'N/A')
                            sport = g.get('sport', {}).get('name', 'N/A')
                            sport_id = g.get('sportId')
                            league = g.get('league', {}).get('name', 'N/A')
                            
                            # Filtro diagnostico per l'utente
                            if any(kw in title.lower() for kw in ["bitcoin", "eth", "doge", "xrp", "sol"]):
                                print(f"    🎯 [TARGET!] {title} | SportID: {sport_id} | League: {league}")
                                found_any = True
                            elif "up" in title.lower() or "down" in title.lower() or "predict" in title.lower():
                                print(f"    ⭐ [PREDICT?] {title} | SportID: {sport_id}")
                                found_any = True
                else:
                    print(f"  ❌ Error {resp.status_code}")
            except Exception as e:
                print(f"  ⚠ Exception: {e}")

    if not found_any:
        print("\n❌ Nessun mercato Crypto/Predict trovato con i filtri standard.")
        print("Suggerimento: Provare l'endpoint /market-manager/navigation con headers.")

if __name__ == "__main__":
    deep_scan()
