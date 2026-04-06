import requests
import json

# Subgraph Azuro V3 per Polygon
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

def discover_all_lps():
    print("=== DISCOVERING ALL ACTIVE LPs: Azuro V3 ===")
    
    # Cerchiamo le ultime 200 condizioni create su Polygon
    query = """
    {
      conditions(first: 200, orderBy: id, orderDirection: desc) {
        liquidityPool
        game {
          title
          sport { id name }
          league { id name }
        }
      }
    }
    """
    
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            conds = resp.json().get('data', {}).get('conditions', [])
            if conds:
                lps = {}
                for c in conds:
                    lp = c['liquidityPool']
                    title = c['game']['title']
                    sport = c['game']['sport']['name']
                    
                    if lp not in lps:
                        lps[lp] = []
                    lps[lp].append(f"[{sport}] {title}")
                
                print(f"✅ TROVATE {len(lps)} POOL ATTIVE!")
                for lp, items in lps.items():
                    print(f"\n📍 LP: {lp}")
                    print(f"   Esempi (primi 3):")
                    for item in items[:3]:
                        print(f"    - {item}")
                    
                    if any(kw in " ".join(items).lower() for kw in ["xrp", "doge", "bit", "eth", "up", "down", "predict"]):
                        print("   🎯 [TARGET MATCH!] Questa pool ha mercati Crypto/Prediction.")
                        return lp
            else:
                print("❌ Nessuna condizione trovata negli ultimi 200 record del subgraph.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

if __name__ == "__main__":
    correct_lp = discover_all_lps()
    if correct_lp:
        print(f"\n🚀 POOL DA USARE: {correct_lp}")
    else:
        print("\n❌ Non è stato possibile trovare una pool con mercati Crypto.")
