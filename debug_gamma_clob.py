"""
debug_gamma_clob.py — Trova eventi attuali via Gamma e verifica che abbiano token CLOB
"""
import requests, json

print("=== Gamma Events con volume alto (attuali) ===")
resp = requests.get("https://gamma-api.polymarket.com/events", params={
    "active": "true",
    "closed": "false",
    "limit": 20
})
events = resp.json()

tradeable = []
for event in events:
    if not isinstance(event, dict):
        continue
    markets = event.get("markets", [])
    for m in markets:
        if not isinstance(m, dict):
            continue
        clob_ids_raw = m.get("clobTokenIds")
        if not clob_ids_raw:
            continue
        try:
            clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
        except Exception:
            continue
        if len(clob_ids) >= 2:
            tradeable.append({
                "event": event.get("title", "?"),
                "question": m.get("question", "?"),
                "volume": float(m.get("volume") or 0),
                "volume24hr": float(event.get("volume24hr") or 0),
                "outcomePrices": m.get("outcomePrices"),
                "outcomes": m.get("outcomes"),
                "yes_token": clob_ids[0],
                "no_token": clob_ids[1],
                "conditionId": m.get("conditionId","?"),
            })

# Ordina per volume 24h
tradeable.sort(key=lambda x: x["volume24hr"], reverse=True)

print(f"Mercati con clobTokenIds: {len(tradeable)}")
print()
for t in tradeable[:10]:
    print(f"EVENT:    {t['event'][:60]}")
    print(f"QUESTION: {t['question'][:70]}")
    print(f"Volume24h: {t['volume24hr']:.0f} USDC")
    print(f"Prices:   {t['outcomePrices']}")
    print(f"YES token: {t['yes_token'][:40]}...")
    print(f"NO  token: {t['no_token'][:40]}...")
    print()

    # Verifica che il token sia quotato sul CLOB
    try:
        r = requests.get(f"https://clob.polymarket.com/book", params={"token_id": t["yes_token"]}, timeout=5)
        book = r.json()
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        if bids or asks:
            print(f"  >> CLOB OK: {len(bids)} bids, {len(asks)} asks")
            if bids:
                print(f"     Best bid: {bids[0]}")
            if asks:
                print(f"     Best ask: {asks[0]}")
        else:
            print(f"  >> CLOB: orderbook vuoto")
    except Exception as e:
        print(f"  >> CLOB errore: {e}")
    print("-" * 60)
