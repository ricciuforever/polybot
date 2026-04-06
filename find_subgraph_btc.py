import requests
import json
import time

SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
TIMESTAMP = 1775480400 # Da dgpredict.com/app/event/btc-updown-5m-1775480400

query = """
{
  games(where: { startsAt: %d }) {
    id
    gameId
    title
    sport { name }
    league { name }
    conditions {
      id
      conditionId
      status
      outcomes {
        outcomeId
        currentOdds
      }
    }
  }
}
""" % TIMESTAMP

def search_subgraph_by_timestamp():
    print(f"--- AZURO SUBGRAPH SEARCH BY TIMESTAMP: {TIMESTAMP} ---")
    try:
        response = requests.post(SUBGRAPH_URL, json={'query': query}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            games = data.get('data', {}).get('games', [])
            if games:
                print(f"Trovati {len(games)} giochi con timestamp {TIMESTAMP}:")
                for g in games:
                    print(json.dumps(g, indent=2))
            else:
                print(f"Nessun gioco trovato con startsAt = {TIMESTAMP}.")
                # Proviamo a cercare tra i giochi creati di recente o con title_contains "Bitcoin"
                print("\nEseguo ricerca per titolo 'Bitcoin' nel Subgraph...")
                search_title_query = """
                {
                  games(where: { title_contains_nocase: "Bitcoin" }, first: 10, orderBy: startsAt, orderDirection: desc) {
                    id
                    gameId
                    title
                    startsAt
                    conditions {
                      conditionId
                      status
                    }
                  }
                }
                """
                resp2 = requests.post(SUBGRAPH_URL, json={'query': search_title_query}, timeout=15)
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    games2 = data2.get('data', {}).get('games', [])
                    if games2:
                        print(f"Trovati {len(games2)} giochi con titolo Bitcoin:")
                        for g in games2:
                            print(f"- {g['title']} (Starts: {g['startsAt']} | ID: {g['gameId']})")
                    else:
                        print("Nessun gioco con titolo Bitcoin trovato nel Subgraph.")
        else:
            print(f"Errore HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Errore: {str(e)}")

if __name__ == "__main__":
    search_subgraph_by_timestamp()
