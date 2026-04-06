"""
debug_accepting.py — Trova tutti i mercati che accettano ordini ora.
Usa accepting_orders=true come filtro + get_sampling_markets() 
"""
import os, json, requests
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

load_dotenv()

KEY = os.getenv("HOT_WALLET_PRIVATE_KEY")
client = ClobClient(host="https://clob.polymarket.com", chain_id=137, key=KEY)

# --- Metodo 1: get_sampling_markets() ---
print("=== get_sampling_markets() ===")
try:
    sampling = client.get_sampling_markets(next_cursor="")
    smarkets = sampling.get("data", [])
    print(f"Trovati: {len(smarkets)}")
    for m in smarkets[:5]:
        print(f"  Q: {m.get('question','?')[:70]}")
        print(f"     accepting={m.get('accepting_orders')} | ob={m.get('enable_order_book')}")
except Exception as e:
    print(f"Errore: {e}")

print()

# --- Metodo 2: Scan con accepting_orders ---
print("=== Scan per accepting_orders=True (prime 5 pagine) ===")
accepting = []
cursor = ""
for page in range(5):
    resp = client.get_markets(next_cursor=cursor)
    for m in resp.get("data", []):
        if m.get("accepting_orders"):
            accepting.append(m)
    cursor = resp.get("next_cursor", "")
    if not cursor or cursor == "LTE=":
        break

print(f"Trovati {len(accepting)} mercati che accettano ordini (prime 5 pagine)")
for m in accepting:
    q = m.get("question", "?")
    toks = m.get("tokens", [])
    btc_flag = "** BTC **" if any(k in q.lower() for k in ["bitcoin","btc"]) else ""
    print(f"  {btc_flag} {q[:75]}")
    for t in toks[:2]:
        print(f"    {t.get('outcome','?')}: {t.get('token_id','?')[:40]}...")

print()

# --- Metodo 3: REST diretto con accepting_orders filter ---
print("=== REST: /markets?accepting_orders=true ===")
try:
    r = requests.get("https://clob.polymarket.com/markets", params={"limit":50,"accepting_orders":"true"}, timeout=10)
    data = r.json()
    if isinstance(data, dict):
        ms = data.get("data", [])
        print(f"Trovati: {len(ms)}")
        for m in ms[:5]:
            print(f"  {m.get('question','?')[:70]}")
    else:
        print(data)
except Exception as e:
    print(f"Errore: {e}")
