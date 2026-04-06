import requests
import json

URL = "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

def find_leagues():
    print("=== EXTRACTING ALL LEAGUES FROM AZURO V3 (Polygon) ===\n")
    
    query = """
    {
      leagues(first: 100) {
        id
        leagueId
        name
        sport {
          name
          sportId
        }
      }
    }
    """
    
    try:
        resp = requests.post(URL, json={'query': query}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            leagues = data.get('data', {}).get('leagues', [])
            
            print(f"Trovate {len(leagues)} leagues. Analisi nomi...\n")
            
            for l in leagues:
                name = l.get('name', '')
                if any(x in name.lower() for x in ["bit", "cry", "pre", "finance"]):
                    print(f"✅ TROVATA: {name} | leagueId: {l['leagueId']} | Sport: {l['sport']['name']} (ID: {l['sport']['sportId']})")
                else:
                    # Stampa i primi 5 per debug se non trovi match
                    pass
            
            if not any(any(x in l.get('name', '').lower() for x in ["bit", "cry"]) for l in leagues):
                print("[!] Nessuna league Bitcoin/Crypto trovata tra le prime 100.")
        else:
            print(f"Errore Subgraph: {resp.status_code}")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    find_leagues()
