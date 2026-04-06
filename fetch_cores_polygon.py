import requests
import json

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

query = """
{
  cores {
    id
    address
    type
  }
}
"""

def fetch_cores():
    print(f"--- FETCHING CORES ON POLYGON V3 ---")
    try:
        response = requests.post(SUBGRAPH_URL, json={'query': query}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            cores = data.get('data', {}).get('cores', [])
            for c in cores:
                print(f"- ID: {c['id']} | Address: {c['address']} | Type: {c['type']}")
        else:
            print(f"Error {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    fetch_cores()
