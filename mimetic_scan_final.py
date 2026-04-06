import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def mimetic_scan():
    print("=== FINAL MIMETIC SCAN: PolygonDGEN ===")
    
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    # Testiamo tutti gli stati possibili
    states = ["Created", "Prematch", "Live"]
    
    found_any = False

    for state in states:
        print(f"\n🔍 Analisi GnosisXDAI - {state}...")
        url = f"{BASE_URL}/market-manager/games-by-filters"
        params = {
            "environment": "GnosisXDAI",
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
                        lp = g.get('liquidityPool', 'N/A')
                        
                        if any(kw in title.lower() for kw in ["xrp", "doge", "bit", "eth", "up", "down", "predict"]):
                            print(f"    🎯 [TARGET!] {title}")
                            print(f"       -> SportID: {sport_id} | League: {league}")
                            print(f"       -> LP: {lp}")
                            found_any = True
                else:
                    print(f"  (Nessun gioco in questo stato)")
            else:
                print(f"  ❌ Errore HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"  ⚠ Eccezione: {e}")

    if not found_any:
        print("\n❌ Nessun mercato Crypto trovato nemmeno in PolygonDGEN.")
        print("💡 Suggerimento: Provare l'endpoint /search universale in PolygonDGEN.")

if __name__ == "__main__":
    mimetic_scan()
