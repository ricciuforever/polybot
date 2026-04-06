import requests
import json

# Subgraph Azuro V3 per Polygon
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
SAFE_ADDRESS = "0xF70ce42B1bBEbCc1deEe5315506373Ba7E535e9d".lower()

def spy_safe():
    print(f"=== SPYING SAFE WALLET BETS: {SAFE_ADDRESS} ===")
    
    # Cerchiamo le ultime 20 scommesse piazzate da questo Safe su Azuro V3
    query = """
    query($account: String!) {
      bets(first: 20, where: { account: $account }, orderBy: createdBlockNumber, orderDirection: desc) {
        id
        amount
        game {
          gameId
          title
          startsAt
          sport { id name }
          league { id name }
        }
        liquidityPool
      }
    }
    """
    
    try:
        variables = {"account": SAFE_ADDRESS}
        resp = requests.post(SUBGRAPH_URL, json={"query": query, "variables": variables}, timeout=15)
        if resp.status_code == 200:
            bets = resp.json().get('data', {}).get('bets', [])
            if bets:
                print(f"✅ TROVATE {len(bets)} SCOMMESSE RECENTI!")
                for b in bets:
                    g = b['game']
                    title = g.get('title', 'N/A')
                    sport_id = g.get('sport', {}).get('id', 'N/A')
                    sport_name = g.get('sport', {}).get('name', 'N/A')
                    league_id = g.get('league', {}).get('id', 'N/A')
                    league_name = g.get('league', {}).get('name', 'N/A')
                    lp = b.get('liquidityPool', 'N/A')
                    
                    print(f"\n🎯 SCOMMESSA: {title}")
                    print(f"   SportID: {sport_id} ({sport_name})")
                    print(f"   LeagueID: {league_id} ({league_name})")
                    print(f"   LiquidityPool: {lp}")
                
                # Salviamo i risultati per l'aggiornamento del bot
                return bets[0]
            else:
                print("❌ Nessuna scommessa trovata per questo Safe su Azuro V3 (Polygon).")
                print("💡 Potresti aver scommesso su un altro subgraph o su Gnosis?")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

if __name__ == "__main__":
    last_bet = spy_safe()
    if last_bet:
        print("\n🚀 DATI CATTURATI! Siamo pronti per aggiornare config.py.")
