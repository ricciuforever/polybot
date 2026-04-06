import requests
import json

# Subgraph Azuro V3 su Polygon (il più popolato)
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
LP_ADDRESS = "0x0FA7FB5407eA971694652E6E16C12A52625DE1b8".lower()

def spy_bets():
    print(f"=== SPYING ACTIVE BETS ON LP: {LP_ADDRESS} ===")
    
    # Cerchiamo le ultime 100 scommesse piazzate su questa LP
    query = """
    query($lp: String!) {
      bets(first: 100, where: { liquidityPool: $lp }, orderBy: createdBlockNumber, orderDirection: desc) {
        id
        amount
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
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            bets = resp.json().get('data', {}).get('bets', [])
            if bets:
                print(f"✅ TROVATE {len(bets)} SCOMMESSE RECENTI!")
                crypto_matches = []
                for b in bets:
                    g = b['game']
                    title = g.get('title', 'N/A')
                    sport_id = g.get('sport', {}).get('id', 'N/A')
                    sport_name = g.get('sport', {}).get('name', 'N/A')
                    league_id = g.get('league', {}).get('id', 'N/A')
                    league_name = g.get('league', {}).get('name', 'N/A')
                    
                    print(f"  - Bet on: {title} | Sport: {sport_id} ({sport_name}) | League: {league_id} ({league_name})")
                    
                    if any(kw in title.lower() for kw in ["bit", "eth", "xrp", "doge", "up", "down", "predict"]):
                        crypto_matches.append(g)
                
                if crypto_matches:
                    print("\n🎯 [BINGO!] TROVATI MERCATI CRYPTO:")
                    for m in crypto_matches[:5]:
                        print(f"   -> {m['title']} | SportID: {m['sport']['id']} | LeagueID: {m['league']['id']}")
                else:
                    print("\n❌ Nessuna scommessa su Crypto in questo pool.")
            else:
                print("❌ Nessuna scommessa piazzata di recente su questo LP (controllato azuro-api-polygon-v3).")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    spy_bets()
