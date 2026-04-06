import requests
import json

# Subgraph client per metadati (leagues, sports)
SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

def find_league():
    print("=== SEARCHING FOR CRYPTO LEAGUE ID: AZURO V3 ===")
    
    # Cerchiamo XRP in tutti i nomi delle leghe
    query = """
    {
      leagues(first: 100, where: { name_contains_nocase: "XRP" }) {
        id
        name
        sport { id name }
      }
    }
    """
    
    try:
        resp = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            leagues = resp.json().get('data', {}).get('leagues', [])
            if leagues:
                for l in leagues:
                    print(f"✅ TROVATA LEAGUE: {l['name']} (ID: {l['id']})")
                    print(f"   Sport: {l['sport']['name']} (ID: {l['sport']['id']})")
                return leagues[0]
            else:
                # Provo con "Bitcoin"
                print("⚠️ XRP non trovato, provo con 'Bitcoin'...")
                query_btc = '{ leagues(first: 100, where: { name_contains_nocase: "Bitcoin" }) { id name sport { id name } } }'
                resp2 = requests.post(SUBGRAPH_URL, json={"query": query_btc}, timeout=15)
                leagues2 = resp2.json().get('data', {}).get('leagues', [])
                if leagues2:
                    for l in leagues2:
                        print(f"✅ TROVATA LEAGUE: {l['name']} (ID: {l['id']})")
                        print(f"   Sport: {l['sport']['name']} (ID: {l['sport']['id']})")
                    return leagues2[0]
                else:
                    print("❌ Nessuna categoria 'Crypto' trovata per nome.")
        else:
            print(f"Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    return None

if __name__ == "__main__":
    find_league()
