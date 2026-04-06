import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"

query = """
{
  leagues(first: 100, where: { name_contains_nocase: "bit" }) {
    id
    name
    sport { id name }
  }
}
"""

def find_league():
    print("=== SEARCHING FOR CRYPTO LEAGUES: Azuro V3 ===")
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            leagues = resp.json().get('data', {}).get('leagues', [])
            if leagues:
                for l in leagues:
                    print(f"✅ TROVATA LEAGUE: {l['name']} (ID: {l['id']})")
                    print(f"   Sport: {l['sport']['name']} (ID: {l['sport']['id']})")
            else:
                # Provo broad "predict"
                print("Provo ricerca per 'predict'...")
                query_predict = '{ leagues(first: 100, where: { name_contains_nocase: "predict" }) { id name sport { id name } } }'
                resp2 = requests.post(SUBGRAPH_URL, json={"query": query_predict}, timeout=15)
                leagues2 = resp2.json().get('data', {}).get('leagues', [])
                for l in leagues2:
                    print(f"✅ TROVATA LEAGUE: {l['name']} (ID: {l['id']})")
                    print(f"   Sport: {l['sport']['name']} (ID: {l['sport']['id']})")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    find_league()
