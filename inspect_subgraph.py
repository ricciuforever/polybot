import requests
import json
import config

def inspect_game_schema():
    subgraph = config.AZURO_SUBGRAPH
    print(f"--- INSPECTING GAME SCHEMA ON {subgraph} ---")
    
    # Cerchiamo un gioco qualsiasi per vedere i campi
    query = """
    {
      games(first: 1) {
        id
        gameId
        title
        status
        # Proviamo anche altri nomi comuni per lo stato
        # state
      }
    }
    """
    try:
        resp = requests.post(subgraph, json={'query': query}, timeout=15)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
        
        # Se fallisce con "status" non esistente, proviamo "state"
        if "errors" in resp.json():
            print("\nRetrying with 'state'...")
            query2 = """
            {
              games(first: 1) {
                id
                gameId
                title
                state
              }
            }
            """
            resp2 = requests.post(subgraph, json={'query': query2}, timeout=15)
            print(json.dumps(resp2.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_game_schema()
