import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"

# Cerchiamo tutte le condizioni in Created o Live, ignorando l'LP predefinito
query = """
{
  conditions(first: 200, where: { status_in: [Created, Live] }) {
    id
    liquidityPool
    game {
      title
      sport { name }
      league { name }
    }
  }
}
"""

def find_lp():
    print("=== SEARCHING FOR CORRECT AZURO LP (Polygon) ===")
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            conds = resp.json().get('data', {}).get('conditions', [])
            if not conds:
                print("⚠️ Nessuna condizione attiva trovata (Azuro potrebbe essere in manutenzione o URL errato).")
                return

            lp_data = {}
            for c in conds:
                lp = c['liquidityPool']
                title = c['game']['title']
                sport = c['game']['sport']['name']
                
                if lp not in lp_data:
                    lp_data[lp] = []
                lp_data[lp].append(f"[{sport}] {title}")
            
            for lp, items in lp_data.items():
                print(f"\n📍 LP ADDRESS DISCOVERED: {lp}")
                print(f"   Esempi mercati ({len(items)}):")
                for item in items[:3]:
                    print(f"    - {item}")
                
                if any(kw in " ".join(items).lower() for kw in ["xrp", "doge", "bit", "eth", "up", "down"]):
                    print("   🎯 [TARGET MATCH!] Questa è la pool di DGPredict!")
                    return lp
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

if __name__ == "__main__":
    correct_lp = find_lp()
    if correct_lp:
        print(f"\n✅ LP DA USARE: {correct_lp}")
    else:
        print("\n❌ Non è stato possibile trovare una pool con mercati Crypto.")
