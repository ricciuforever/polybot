import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"
ENV = "PolygonUSDT"

def debug_raw():
    # Usiamo /top-games per vedere se i mercati Bitcoin sono lì (essendo popolari)
    url = f"{BASE_URL}/market-manager/top-games"
    params = {"environment": ENV}

    print(f"--- AZURO TOP GAMES SCANNER ---")
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for i, g in enumerate(data):
                title = g.get('title', 'N/A')
                sport = g.get('sport', {}).get('name', 'N/A')
                print(f"[{i+1}] {title} (Sport: {sport})")
                if "Bitcoin" in title or "Up" in title:
                    print(f"    >>> TROVATO!")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

    try:
        resp = requests.get(url, params=params, timeout=15)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if "games" in data:
                games = data.get("games", [])
                print(f"Trovati {len(games)} giochi.\n")
                for i, g in enumerate(games):
                    sport = g.get('sport', {}).get('name', 'N/A')
                    title = g.get('title', 'N/A')
                    game_id = g.get('gameId', 'N/A')
                    print(f"[{i+1}] Sport: {sport} | Title: {title} | ID: {game_id}")
            else:
                print("Chiave 'games' non trovata. Mostro JSON completo:\n")
                print(json.dumps(data, indent=2))
        else:
            print(f"Response Error: {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_raw()
