import requests
import json
import time

# Base URL per la Backend API Azuro V3 Beta
BASE_URL = "https://api.onchainfeed.org/api/v1/public"

# Possibili environment per Polygon
# Proviamo PolygonUSDT (nome interno API per USDC.e su Polygon)
ENV = "PolygonUSDT" 

def debug_api():
    print(f"--- AZURO V3 REST API DEBUG ---")
    print(f"Target Environment: {ENV}")

    # 1. TEST SEARCH ENDPOINT
    search_url = f"{BASE_URL}/market-manager/search"
    params = {
        "environment": ENV,
        "request": "BTC",
        "page": 1,
        "perPage": 5
    }

    print(f"\n[1] Cerco mercati BTC tramite /search...")
    try:
        resp = requests.get(search_url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            games = data.get("games", [])
            print(f"Trovati {len(games)} giochi.")
            for g in games:
                print(f"- ID: {g.get('id')} | Title: {g.get('title')} | State: {g.get('state')} | StartsAt: {g.get('startsAt')}")
                # Cerchiamo le condizioni se presenti nel record del gioco
                # In V3, a volte sono in un endpoint separato
        else:
            print(f"Errore {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Errore durante la search: {e}")

    # 2. TEST GAMES-BY-FILTERS
    filters_url = f"{BASE_URL}/market-manager/games-by-filters"
    params = {
        "environment": ENV,
        "gameState": "Prematch",
        "orderBy": "startsAt",
        "orderDirection": "asc",
        "page": 1,
        "perPage": 10
    }

    print(f"\n[2] Cerco giochi Prematch generici...")
    try:
        resp = requests.get(filters_url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            games = data.get("games", [])
            print(f"Trovati {len(games)} giochi Prematch.")
            if games:
                # Mostriamo il primo gioco in dettaglio per capire la struttura
                print("\nEsempio struttura di un gioco:")
                print(json.dumps(games[0], indent=2))
        else:
            print(f"Errore {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Errore durante i filtri: {e}")

    # 3. TEST CONDITIONS (Se abbiamo un gioco)
    # Se abbiamo trovato un gioco al punto 1 o 2, chiediamo le condizioni
    # Usiamo un ID fittizio o reale se l'abbiamo
    if 'games' in locals() and games:
        game_id = games[0].get('id')
        if game_id:
            conditions_url = f"{BASE_URL}/market-manager/conditions-by-game-ids"
            payload = {
                "environment": ENV,
                "gameIds": [game_id]
            }
            print(f"\n[3] Recupero condizioni per Game ID {game_id} via POST...")
            try:
                resp = requests.post(conditions_url, json=payload, timeout=10)
                if resp.status_code == 200:
                    cond_data = resp.json()
                    print("\nStruttura Condizioni:")
                    print(json.dumps(cond_data, indent=2))
                else:
                    print(f"Errore {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"Errore durante recupero condizioni: {e}")

if __name__ == "__main__":
    debug_api()
