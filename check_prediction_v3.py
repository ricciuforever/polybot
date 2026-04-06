import requests
import json

CONDITION_ID = "0xa572772bf7a4a3700cbc55ceca268c062968d11ac9ade030a4e046c476c5baf5"
URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-prediction-v3"

def check():
    query = """
    {
      condition(id: "%s") {
        id
        status
        outcomes {
          outcomeId
          currentOdds
        }
      }
    }
    """ % CONDITION_ID
    
    try:
        resp = requests.post(URL, json={'query': query}, timeout=15)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
