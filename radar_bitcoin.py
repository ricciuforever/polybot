import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

print("=== SCANSIONE BRUTA AZURO V3 (PARAMETRI OBBLIGATORI) ===\n")

# Parametri richiesti esplicitamente dall'errore 400
params = {
    "gameState": "Prematch",        # Obbligatorio
    "environment": "PolygonUSDT",    # Obbligatorio (quello del tuo config.py)
    "orderBy": "startsAt",          # Obbligatorio
    "orderDirection": "asc",        # Obbligatorio
    "page": 1,                      # Obbligatorio
    "perPage": 50                   # Massimo consigliato per pagina
}

try:
    url = f"{BASE_URL}/market-manager/games-by-filters"
    print(f"Interrogazione endpoint: {url}")
    
    # Molti di questi endpoint preferiscono la GET con parametri nella URL
    resp = requests.get(url, params=params, timeout=15)
    
    if resp.status_code == 200:
        data = resp.json()
        # Nella V3 i giochi sono solitamente sotto 'games' o 'items'
        games = data.get("games", []) or data.get("items", [])
        
        print(f"Scaricati {len(games)} giochi totali.\n")
        
        found = False
        for g in games:
            title = g.get('title', '')
            # Cerchiamo Bitcoin ignorando maiuscole/minuscole
            if "bitcoin" in title.lower():
                print(f"✅ TROVATO: {title}")
                print(f"   -> GameID: {g.get('gameId')}")
                print(f"   -> SportID: {g.get('sportId')}")
                print(f"   -> LeagueID: {g.get('leagueId')}")
                print(f"   -> StartsAt: {g.get('startsAt')}\n")
                found = True
        
        if not found:
            print("❌ Bitcoin non trovato tra i primi 50 giochi Prematch.")
            print("Esempi di titoli trovati per debug:")
            for g in games[:10]:
                print(f"   - {g.get('title')} (ID: {g.get('gameId')})")
    else:
        print(f"Errore API: {resp.status_code}")
        print(f"Dettagli: {resp.text}")

except Exception as e:
    print(f"Errore script: {e}")