import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def map_navigation():
    print("=== NAVIGAZIONE AZURO V3: RICERCA CATEGORIE CRYPTO/BITCOIN ===")
    
    url = f"{BASE_URL}/market-manager/navigation"
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
    }
    params = {"environment": "PolygonUSDT"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            
            # La struttura di navigazione in V3 è un dizionario con chiave 'sports'
            sports_list = data.get('sports', [])
            
            found = False
            for sport in sports_list:
                sport_name = sport.get('name', '')
                sport_id = sport.get('sportId')
                
                # Cerchiamo nei nomi degli sport
                if any(x in sport_name.lower() for x in ["crypto", "bit", "pre", "finance"]):
                    print(f"\n[!] VINCITORE (Sport): {sport_name} | sportId: {sport_id}")
                    found = True
                
                # Esploriamo le categorie/paesi (spesso chiamate 'countries' o 'categories')
                for country in sport.get('countries', []):
                    # Esploriamo le league
                    for league in country.get('leagues', []):
                        league_name = league.get('name', '')
                        league_id = league.get('leagueId')
                        
                        if any(x in league_name.lower() for x in ["bit", "crypto", "up", "predict"]):
                            print(f" -> League Trovata: {league_name} | leagueId: {league_id} (Sotto Sport: {sport_name} ID: {sport_id})")
                            found = True
            
            if not found:
                print("\n[?] Nessun match diretto per 'Bitcoin' o 'Crypto' nella navigazione.")
                print("Ecco i primi 5 sport per debugging:")
                for s in data[:5]:
                    print(f"- {s.get('name')} (ID: {s.get('sportId')})")
        else:
            print(f"Errore API: Status {resp.status_code}")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    map_navigation()
