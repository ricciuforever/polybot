import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def brute_force():
    print("=== BRUTE FORCE GAMES: RICERCA ID BITCOIN (Azuro V3) ===\n")
    
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
    }
    
    url = f"{BASE_URL}/market-manager/games-by-filters"
    
    # Parametri necessari per Azuro V3 (Polygon)
    params = {
        "environment": "PolygonUSDT",
        "gameState": "Prematch",
        "perPage": 50,
        "page": 1,
        "orderBy": "startsAt",
        "orderDirection": "asc"
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            # In V3 la risposta di games-by-filters solitamente ha una chiave 'items'
            games = data.get('items', [])
            
            print(f"Scaricati {len(games)} giochi. Analisi in corso...\n")
            
            found_any = False
            for g in games:
                title = g.get('title', 'N/A')
                sport_id = g.get('sportId')
                # In alcuni casi leagueId è un oggetto o 'league' { 'id': ... }
                # Verifichiamo la struttura
                league = g.get('league', {})
                league_id = g.get('leagueId') or league.get('id')
                
                output_line = f"-> {title} | SportId: {sport_id} | LeagueId: {league_id}"
                
                if "bitcoin" in title.lower():
                    print(f"\033[92m{output_line} [MATCH!]\033[0m") # Verde per il match
                    found_any = True
                else:
                    print(output_line)
            
            if not found_any:
                print("\n[!] Nessun gioco 'Bitcoin' trovato nei primi 50 risultati.")
                print("Suggerimento: Prova a cambiare orderBy in 'turnover' o aumenta perPage.")
        else:
            print(f"Errore API: Status {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    brute_force()
