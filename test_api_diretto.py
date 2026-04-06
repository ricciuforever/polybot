import requests

print("=== HACKING THE MAINFRAME: RICERCA MAPPA API AZURO ===")

# Proviamo tutti gli indirizzi dove Azuro potrebbe aver pubblicato il file Swagger JSON
urls_da_provare = [
    "https://api.onchainfeed.org/api/v1/public/gateway/docs-json",
    "https://api.onchainfeed.org/api/v1/public/docs-json",
    "https://api.onchainfeed.org/api-json",
    "https://api.onchainfeed.org/api/v1/public/swagger-json",
    "https://dev-api.onchainfeed.org/api/v1/public/gateway/docs-json"
]

mappa_trovata = False

for url in urls_da_provare:
    print(f"Provo a leggere la mappa da: {url}")
    try:
        resp = requests.get(url)
        if resp.status_code == 200 and "paths" in resp.json():
            print("\n✅ MAPPA (SWAGGER) SCARICATA CON SUCCESSO!\n")
            data = resp.json()
            paths = data.get("paths", {})
            
            print("--- ENDPOINT DISPONIBILI (Filtrati per Games/Sports/Markets) ---")
            for path, methods in paths.items():
                path_lower = path.lower()
                # Mostriamo solo le rotte utili per cercare i mercati
                if any(chiave in path_lower for chiave in ["game", "sport", "event", "market", "condition", "search"]):
                    # Stampa i metodi disponibili (GET, POST) e l'endpoint
                    print(f"-> [{', '.join(methods.keys()).upper()}] {path}")
            
            mappa_trovata = True
            break
        else:
            print(f"   -> Niente mappa qui (Status {resp.status_code})")
    except Exception as e:
        print(f"   -> Errore di connessione: {e}")

if not mappa_trovata:
    print("\n[!] Impossibile trovare il file Swagger automatico. Dovremo usare l'endpoint GraphQL o un'altra via.")