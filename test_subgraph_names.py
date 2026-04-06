import requests

NAMES = [
    "azuro-api-polygon-v3",
    "azuro-v3-polygon",
    "azuro-data-feed-polygon",
    "azuro-data-feed-v3-polygon",
    "azuro-protocol-v3-polygon"
]

def test_names():
    print("=== TESTING SUBGRAPHS AZURO V3 ===")
    for name in NAMES:
        url = f"https://thegraph.azuro.org/subgraphs/name/azuro-protocol/{name}"
        query = "{ games(first: 1) { id } }"
        try:
            resp = requests.post(url, json={"query": query}, timeout=5)
            if resp.status_code == 200:
                print(f"✅ VALIDO: {name}")
                # Verifica se ha giochi recenti
                query_recent = "{ games(first: 5, orderBy: startsAt, orderDirection: desc) { title } }"
                resp2 = requests.post(url, json={"query": query_recent}, timeout=5)
                games = resp2.json().get('data', {}).get('games', [])
                if games:
                    print(f"   -> Ultimi giochi: {games[0]['title']}")
                else:
                    print("   -> (Nessun gioco trovato in questo subgraph)")
            else:
                # print(f"❌ Errore {name}: {resp.status_code}")
                pass
        except:
            pass

if __name__ == "__main__":
    test_names()
