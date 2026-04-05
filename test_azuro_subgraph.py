import requests
import json

# Nuovo endpoint raccomandato per Azuro V3
API_URL = "https://api.onchainfeed.org/api/v1/public/gateway/graphql"

query = """
query {
  games(
    where: { 
      status: Created,
      OR: [
        { title_contains: "Bitcoin" },
        { title_contains: "BTC" },
        { sport: { name_contains: "Crypto" } }
      ]
    }
  ) {
    id
    title
    startsAt
    sport { name }
    conditions {
      id
      conditionId
      outcomes {
        id
        outcomeId
        currentOdds
      }
    }
  }
}
"""

def fetch_crypto_markets():
    try:
        # Nota: L'API Backend usa spesso GraphQL o REST. Proviamo GraphQL sul gateway.
        response = requests.post(API_URL, json={'query': query}, timeout=15)
        if response.status_code != 200:
            print(f"Status Code: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_crypto_markets()
