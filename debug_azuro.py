import requests
import json

DATA_FEED_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

def query_azuro(query):
    try:
        response = requests.post(DATA_FEED_URL, json={'query': query}, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # 1. Vediamo gli sport
    sports_data = query_azuro("{ sports { id name } }")
    print("--- SPORTS ---")
    print(json.dumps(sports_data, indent=2))
    
    # 2. Cerchiamo Bitcoin nel titolo di TUTTI i giochi (anche completati per debug)
    search_query = """
    {
      games(where: { title_contains: "Bitcoin" }) {
        id
        title
        status
        sport { name }
      }
    }
    """
    search_data = query_azuro(search_query)
    print("\n--- SEARCH BITCOIN ---")
    print(json.dumps(search_data, indent=2))
