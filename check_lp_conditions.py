import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"
LP_ADDRESS = "0x0FA7FB5407eA971694652E6E16C12A52625DE1b8".lower()

query = """
query($lp: String!) {
  conditions(first: 50, where: { liquidityPool: $lp, status: Created }) {
    id
    conditionId
    game {
      id
      gameId
      title
      startsAt
      sport { name }
      league { name }
    }
    outcomes {
      outcomeId
    }
  }
}
"""

def scan_lp():
    print(f"=== SCAN LP CONDITIONS: {LP_ADDRESS} ===")
    try:
        variables = {"lp": LP_ADDRESS}
        resp = requests.post(SUBGRAPH_URL, json={"query": query, "variables": variables}, timeout=15)
        if resp.status_code == 200:
            conds = resp.json().get('data', {}).get('conditions', [])
            if conds:
                print(f"✅ TROVATE {len(conds)} CONDIZIONI ATTIVE sull'LP!")
                for c in conds:
                    g = c['game']
                    print(f"  - [{g['sport']['name']}] {g['title']} | GameID: {g['gameId']} | ConditionID: {c['conditionId']}")
            else:
                print("Nessuna condizione attiva (status: Created) su questo LP.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    scan_lp()
