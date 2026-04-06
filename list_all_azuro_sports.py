import requests
import json

# Subgraph Azuro V3 su Polygon
SUBGRAPH_V3 = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
# Subgraph Azuro V2 su Polygon (per verifica)
SUBGRAPH_V2 = "https://api.thegraph.com/subgraphs/name/azuro-protocol/azuro-api-polygon"

def list_sports():
    print("=== LIST ALL SPORTS: Azuro V3 (Polygon) ===")
    query = "{ sports(first: 100) { id name } }"
    
    try:
        resp = requests.post(SUBGRAPH_V3, json={"query": query}, timeout=15)
        if resp.status_code == 200:
            sports = resp.json().get('data', {}).get('sports', [])
            if sports:
                for s in sports:
                    print(f"ID: {s['id']:<5} | Nome: {s['name']}")
                    if any(kw in s['name'].lower() for kw in ["cry", "fin", "pre", "bit", "bin"]):
                        print(f"   🎯 [POSSIBILE MATCH!] Categoria: {s['name']}")
            else:
                print("❌ Nessuno sport trovato in V3.")
        else:
            print(f"Error V3 {resp.status_code}")
            
        print("\n=== LIST ALL SPORTS: Azuro V2 (Polygon) ===")
        resp_v2 = requests.post(SUBGRAPH_V2, json={"query": query}, timeout=15)
        if resp_v2.status_code == 200:
            sports_v2 = resp_v2.json().get('data', {}).get('sports', [])
            if sports_v2:
                for s in sports_v2:
                    print(f"ID: {s['id']:<5} | Nome: {s['name']}")
                    if any(kw in s['name'].lower() for kw in ["cry", "fin", "pre", "bit", "bin"]):
                        print(f"   🎯 [MATCH IN V2!] Categoria: {s['name']}")
            else:
                print("❌ Nessuno sport trovato in V2.")
        else:
            print(f"Error V2 {resp_v2.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_sports()
