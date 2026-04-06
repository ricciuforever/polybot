import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def check_game(game_id):
    print(f"=== CHECK GAME ID: {game_id} ===")
    
    # In V3, l'ID potrebbe essere cercato tramite l'endpoint game-by-id
    # o tramite conditions-by-game-ids
    
    envs = ["PolygonUSDT", "PolygonDGEN", "GnosisXDAI", "ArbitrumUSDT", "BscUSDT"]
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/"
    }
    
    for env in envs:
        print(f"\nTentativo in {env}...")
        # L'endpoint corretto per singola partita in V3 spesso richiede environment
        url = f"{BASE_URL}/market-manager/game-by-id"
        params = {
            "gameId": game_id,
            "environment": env
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                game = resp.json()
                print(f"✅ TROVATO in {env}!")
                print(json.dumps(game, indent=2))
                return
            else:
                print(f"  Status {resp.status_code} ({resp.reason})")
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    check_game("1775513100")
