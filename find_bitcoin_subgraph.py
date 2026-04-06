import requests
import json

# Proviamo a interrogare direttamente il Subgraph (Onchainfeed) per trovare QUALSIASI gioco Bitcoin
URL = "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

def find_any_bitcoin():
    print("=== SEARCHING THE GRAPH FOR BITCOIN (Azuro V3 Polygon) ===\n")
    
    query = """
    {
      games(where: {title_contains_nocase: "Bitcoin"}, first: 20) {
        id
        gameId
        title
        sport {
          name
          sportId
        }
        league {
          name
          leagueId
        }
      }
    }
    """
    
    try:
        resp = requests.post(URL, json={'query': query}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            games = data.get('data', {}).get('games', [])
            
            if not games:
                print("[!] Nessun gioco trovato con 'Bitcoin' nel Subgraph.")
                # Proviamo a vedere gli ultimi 10 giochi creati per capire gli IDs
                print("\n--- Ultimi 10 Giochi Creati ---")
                query_last = """{ games(first: 10, orderBy: gameId, orderDirection: desc) { title sport { name sportId } league { name leagueId } } }"""
                resp_last = requests.post(URL, json={'query': query_last})
                for g in resp_last.json().get('data', {}).get('games', []):
                    print(f"-> {g['title']} | Sport: {g['sport']['name']} ({g['sport']['sportId']}) | League: {g['league']['name']} ({g['league']['leagueId']})")
            else:
                for g in games:
                    print(f"[MATCH] {g['title']}")
                    print(f"   Sport: {g['sport']['name']} (ID: {g['sport']['sportId']})")
                    print(f"   League: {g['league']['name']} (ID: {g['league']['leagueId']})")
        else:
            print(f"Errore Subgraph: {resp.status_code}")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    find_any_bitcoin()
