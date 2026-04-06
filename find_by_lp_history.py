import requests
import json

# Subgraph Azuro V3 su Polygon (il più popolato)
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
LP_ADDRESS = "0x0FA7FB5407eA971694652E6E16C12A52625DE1b8".lower()

def find_lp_history():
    print(f"=== SCANNING LP HISTORY: {LP_ADDRESS} ===")
    
    # Cerchiamo tutte le condizioni legate a questa LP, senza filtri di stato o titolo
    query = """
    query($lp: String!) {
      conditions(first: 100, where: { liquidityPool: $lp }, orderBy: id, orderDirection: desc) {
        id
        conditionId
        status
        game {
          gameId
          title
          startsAt
          sport { id name }
          league { id name }
        }
      }
    }
    """
    
    try:
        variables = {"lp": LP_ADDRESS}
        resp = requests.post(SUBGRAPH_URL, json={"query": query, "variables": variables}, timeout=15)
        if resp.status_code == 200:
            conds = resp.json().get('data', {}).get('conditions', [])
            if conds:
                print(f"✅ TROVATE {len(conds)} CONDIZIONI!")
                found_crypto = False
                for c in conds:
                    g = c['game']
                    title = g.get('title', 'N/A')
                    sport_id = g.get('sport', {}).get('id', 'N/A')
                    sport_name = g.get('sport', {}).get('name', 'N/A')
                    league_id = g.get('league', {}).get('id', 'N/A')
                    league_name = g.get('league', {}).get('name', 'N/A')
                    
                    print(f"  - [{sport_name}] {title} | Status: {c['status']}")
                    print(f"    SportID: {sport_id} | LeagueID: {league_id} ({league_name})")
                    
                    if any(kw in title.lower() for kw in ["bit", "eth", "xrp", "doge", "up", "down", "predict"]):
                        print("    🎯 [TARGET MATCH!] Trovato mercato Crypto.")
                        found_crypto = True
                
                if not found_crypto:
                    print("\n❌ Nessun mercato Crypto nello storico di questa LP (forse l'LP è sbagliata per DGPredict).")
            else:
                print("❌ Nessuna condizione trovata nello storico di questa LP.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_lp_history()
