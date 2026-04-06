import requests
import json

urls = [
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-express-v3",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-prediction-v3",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3-odds",
    "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3",
    "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3-odds"
]

def scan():
    print("=== SCANNING AZURO V3 SUBGRAPHS (Polygon) ===\n")
    query = "{ _meta { block { number } } }"
    
    for url in urls:
        print(f"Testing {url}...")
        try:
            resp = requests.post(url, json={'query': query}, timeout=10)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  ✅ SUCCESS! Block: {resp.json().get('data', {}).get('_meta', {}).get('block', {}).get('number')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    scan()
