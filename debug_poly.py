import requests
import json

def debug_poly():
    url = "https://gamma-api.polymarket.com/markets"
    params = {
        "active": "true",
        "closed": "false",
        "limit": 500,
        "order": "volume",
        "ascending": "false"
    }
    
    print("--- DEBUG POLYMARKET ---")
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Totale Mercati Attivi Trovati: {len(data)}")
        
        crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "doge", "solana", "sol", "ripple", "xrp"]
        
        found = []
        for m in data:
            q = m.get('question', '').lower()
            if any(k in q for k in crypto_keywords):
                if "up or down" in q or "price of" in q:
                    found.append(m['question'])
        
        print(f"Mercati Crypto Filtrati: {len(found)}")
        for f in found[:20]:
            print(f" - {f}")
            
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    debug_poly()
