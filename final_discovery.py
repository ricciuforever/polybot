import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public/market-manager/games-by-filters"

def ultimate_discovery():
    print("=== ULTIMATE DISCOVERY: AZURO V3 PRODUCTION (Polygon USDT) ===\n")
    
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
    }
    
    # Lista di sportId probabili per Predictions
    # 33 (Football), 100 (Politics), 1001 (Finance/Crypto?)
    # Se non mettiamo sportId, cerchiamo in tutto
    
    params = {
        "environment": "PolygonUSDT",
        "gameState": "Prematch",
        "orderBy": "startsAt",
        "orderDirection": "asc",
        "page": 1,
        "perPage": 50
    }
    
    try:
        resp = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            games = data.get('items', [])
            print(f"Scaricati {len(games)} giochi. Ricerca Bitcoin...\n")
            
            for g in games:
                title = g.get('title', '')
                sport = g.get('sport', {})
                league = g.get('league', {})
                
                output = f"-> {title} | Sport: {sport.get('name')} (ID: {g.get('sportId')}) | League: {league.get('name')} (ID: {league.get('id')})"
                
                if "bitcoin" in title.lower() or "ethereum" in title.lower() or "price" in title.lower():
                    print(f"\033[92m{output} [TARGET FOUND!]\033[0m")
                else:
                    # Stampa tutto per debug
                    print(output)
        else:
            print(f"Errore API: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    ultimate_discovery()
