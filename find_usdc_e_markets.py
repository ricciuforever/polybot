import requests
import json

# Subgraph Azuro V3 per Polygon
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
# Token USDC.e su Polygon
USDC_E_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174".lower()

def find_usdc_e_markets():
    print(f"=== SEARCHING USDC.e LPs & MARKETS: {USDC_E_ADDRESS} ===")
    
    # 1. Troviamo tutte le LP che usano USDC.e
    query_lps = """
    query($token: String!) {
      liquidityPools(where: { token: $token }) {
        address
      }
    }
    """
    
    try:
        variables = {"token": USDC_E_ADDRESS}
        resp = requests.post(SUBGRAPH_URL, json={"query": query_lps, "variables": variables}, timeout=15)
        if resp.status_code == 200:
            lps = [lp['address'] for lp in resp.json().get('data', {}).get('liquidityPools', [])]
            if not lps:
                print("❌ Nessuna pool USDC.e trovata su Polygon V3.")
                return

            print(f"✅ TROVATE {len(lps)} POOL USDC.e: {lps}")
            
            # 2. Per ogni pool, cerchiamo le ultime condizioni attive
            for lp in lps:
                print(f"\n🔍 Analisi Pool: {lp}...")
                query_conds = """
                query($lp: String!) {
                  conditions(first: 50, where: { liquidityPool: $lp, status_in: [Created, Live] }) {
                    id
                    game {
                      title
                      sport { name id }
                      league { name id }
                    }
                  }
                }
                """
                variables_conds = {"lp": lp}
                resp_conds = requests.post(SUBGRAPH_URL, json={"query": query_conds, "variables": variables_conds}, timeout=15)
                conds = resp_conds.json().get('data', {}).get('conditions', [])
                
                if conds:
                    found_crypto = False
                    for c in conds:
                        g = c['game']
                        title = g.get('title', 'N/A')
                        sport = g.get('sport', {}).get('name', 'N/A')
                        sport_id = g.get('sport', {}).get('id', 'N/A')
                        league = g.get('league', {}).get('name', 'N/A')
                        league_id = g.get('league', {}).get('id', 'N/A')
                        
                        print(f"  - [{sport}] {title}")
                        print(f"    SportID: {sport_id} | LeagueID: {league_id}")
                        
                        if any(kw in title.lower() for kw in ["xrp", "doge", "bit", "eth", "up", "down", "predict"]):
                            print("    🎯 [BINGO!] Trovato mercato Crypto in questa LP.")
                            found_crypto = True
                    
                    if found_crypto:
                        print(f"\n🚀 POOL PERFETTA TROVATA: {lp}")
                        return lp
                else:
                    print("  ❌ Nessun mercato attivo in questa pool.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

if __name__ == "__main__":
    correct_lp = find_usdc_e_markets()
    if correct_lp:
        print(f"\n✅ USARE QUESTA LP NEL CONFIG: {correct_lp}")
    else:
        print("\n❌ Nessun mercato Crypto trovato nelle pool USDC.e.")
