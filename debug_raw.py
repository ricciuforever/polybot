"""
debug_raw.py — Mostra i campi raw dei primi 5 mercati senza filtri
"""
import os, json
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

load_dotenv()
client = ClobClient(host="https://clob.polymarket.com", chain_id=137, key=os.getenv("HOT_WALLET_PRIVATE_KEY"))

resp = client.get_markets(next_cursor="")
markets = resp.get("data", [])
print(f"Totale nella prima pagina: {len(markets)}")
print(f"next_cursor: {resp.get('next_cursor')}\n")

for m in markets[:3]:
    print("--- MERCATO ---")
    print(json.dumps({
        "question": m.get("question","?")[:80],
        "active": m.get("active"),
        "closed": m.get("closed"),
        "accepting_orders": m.get("accepting_orders"),
        "enable_order_book": m.get("enable_order_book"),
        "minimum_order_size": m.get("minimum_order_size"),
        "condition_id": m.get("condition_id","?")[:20],
        "tokens_count": len(m.get("tokens",[])),
        "first_token": m.get("tokens",[{}])[0].get("token_id","?")[:30] if m.get("tokens") else "none"
    }, indent=2))
    print()

# Conta per stato
active_count = sum(1 for m in markets if m.get("active"))
ob_count = sum(1 for m in markets if m.get("enable_order_book"))
accepting_count = sum(1 for m in markets if m.get("accepting_orders"))
print(f"\nIn questa pagina: active={active_count} | enable_order_book={ob_count} | accepting_orders={accepting_count}")
