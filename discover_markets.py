"""
discover_markets.py — Scansiona tutti i mercati attivi con order book nel CLOB.
Esegui: python discover_markets.py
"""
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

load_dotenv()

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key=os.getenv("HOT_WALLET_PRIVATE_KEY")
)

print("Scansione markets via py-clob-client...")
all_active_ob = []
cursor = ""
pages = 0

while pages < 30:
    try:
        resp = client.get_markets(next_cursor=cursor)
    except Exception as e:
        print(f"Errore pagina {pages}: {e}")
        break

    markets = resp.get("data", [])
    pages += 1

    for m in markets:
        if m.get("active") and m.get("enable_order_book") and not m.get("closed"):
            all_active_ob.append(m)

    cursor = resp.get("next_cursor", "")
    if not cursor or cursor == "LTE=":
        break

    if pages % 5 == 0:
        print(f"  Pagina {pages}... trovati fin qui: {len(all_active_ob)}")

print(f"\nTotale mercati attivi con order book: {len(all_active_ob)} (su {pages} pagine scansionate)\n")

# Mostra tutti quelli trovati
for m in all_active_ob[:20]:
    q = m.get("question", "?")
    cond = m.get("condition_id", "?")
    toks = m.get("tokens", [])
    print(f"Q: {q[:80]}")
    print(f"   conditionId: {cond}")
    for t in toks:
        print(f"   token_id: {t.get('token_id','?')[:50]} | outcome: {t.get('outcome','?')}")
    print()

# Cerca quelli BTC/bitcoin
print("=" * 50)
print("MERCATI BTC/BITCOIN:")
btc = [m for m in all_active_ob if any(k in m.get("question","").lower() for k in ["bitcoin","btc"])]
if btc:
    for m in btc:
        print(f"  >> {m.get('question','?')}")
        for t in m.get("tokens", []):
            print(f"     {t.get('outcome')}: {t.get('token_id','?')}")
else:
    print("  Nessuno trovato.")
