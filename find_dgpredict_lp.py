import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"

query = """
{
  conditions(first: 100, where: { status: Created }) {
    id
    liquidityPool
    game {
      title
      sport { name }
    }
  }
}
"""

def find_lp():
    print("=== SEARCHING FOR DGPredict LP ===")
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            conds = resp.json().get('data', {}).get('conditions', [])
            lps = {}
            for c in conds:
                lp = c['liquidityPool']
                title = c['game']['title']
                sport = c['game']['sport']['name']
                
                if lp not in lps:
                    lps[lp] = []
                lps[lp].append(f"[{sport}] {title}")
            
            for lp, items in lps.items():
                print(f"\nLP: {lp}")
                print(f"  Esempi mercati ({len(items)}):")
                for item in items[:5]:
                    print(f"    - {item}")
                
                if any("bit" in x.lower() or "doge" in x.lower() for x in items):
                    print("    🎯 [TARGET FOUND!] Questo LP ha mercati Crypto.")
            
            if not lps:
                print("Nessuna condizione 'Created' trovata nel subgraph.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_lp()
