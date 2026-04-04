"""
modules/trader.py — Firma e invio ordini a Polymarket via py-clob-client.
Supporto per Proxy Wallet con fallback bilancio blockchain.
"""
import requests
import config
from modules.logger import get_logger
from modules.strategy import BUY_UP, BUY_DOWN, HOLD

log = get_logger("trader")

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds
        
        sig_type = 1 if config.POLY_PROXY_ADDRESS else 0
        funder = str(config.POLY_PROXY_ADDRESS).strip() if sig_type >= 1 else None
        
        creds = ApiCreds(
            api_key=config.POLY_API_KEY,
            api_secret=config.POLY_SECRET,
            api_passphrase=config.POLY_PASSPHRASE,
        )
        
        _client = ClobClient(
            host=config.CLOB_URL, 
            chain_id=config.CHAIN_ID, 
            key=config.PRIVATE_KEY, 
            creds=creds,
            signature_type=sig_type,
            funder=funder
        )
        
        if sig_type >= 1:
            log.info(f"ClobClient inizializzato con Proxy Wallet: {funder} (sig_type={sig_type})")
        else:
            log.info("ClobClient inizializzato come EOA (standard).")
            
    except Exception as e:
        log.error(f"Errore inizializzazione ClobClient: {e}")
    return _client

def get_wallet_balance() -> float | None:
    """Recupera il saldo USDC reale (collateral) via Blockchain (Doppio RPC per affidabilità)."""
    address = config.POLY_PROXY_ADDRESS
    if not address or not address.startswith("0x"): return 0.0

    RPC_URLS = [
        "https://polygon-rpc.com",
        "https://1rpc.io/matic",
        "https://rpc.ankr.com/polygon"
    ]
    
    USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
    clean_addr = address.lower().replace("0x", "")
    data = f"0x70a08231000000000000000000000000{clean_addr}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": USDC_E, "data": data}, "latest"],
        "id": 1
    }

    for rpc in RPC_URLS:
        try:
            r = requests.post(rpc, json=payload, timeout=5)
            if r.status_code == 200:
                res = r.json()
                hex_val = res.get("result")
                if hex_val and isinstance(hex_val, str) and hex_val != "0x":
                    try:
                        raw_val = int(hex_val, 16)
                        bal = round(raw_val / 1_000_000, 2)
                        log.debug(f"Saldo reale recuperato via {rpc}: {bal} USDC")
                        return bal
                    except ValueError:
                        continue
        except Exception as e:
            log.debug(f"Fallito recupero saldo via {rpc}: {e}")
            
    return None

def execute(action: str, token_up: str|None, token_down: str|None, up_price: float, down_price: float, confidence: float) -> bool:
    if action == HOLD: return False
    
    token_id = token_up if action == "BUY_UP" else token_down
    
    # SLIPPAGE AGGRESSIVO (+0.15) per simulare un ordine a MERCATO.
    # Entriamo a qualsiasi prezzo pur di entrare, come richiesto.
    base_price = up_price if action == "BUY_UP" else down_price
    price = round(base_price + 0.15, 2)
    
    # Il prezzo non può superare 0.95 (lasciamo un margine di profitto minimo)
    if price > 0.95: price = 0.95
    
    label = "UP" if action == "BUY_UP" else "DOWN"
    
    if config.DRY_RUN:
        log.info(f"[DRY-RUN] Simulo ordine {label}: {action} @ {price} | Conf: {confidence:.2f}")
        return True

    if not token_id:
        log.error(f"Token ID mancante per {action}")
        return False

    try:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY
        client = _get_client()
        
        # 1. CANCELLIAMO eventuali ordini pendenti prima di procedere per pulire il book
        try:
            client.cancel_all()
            log.debug(f"Pulizia ordini pendenti completata prima di {label}")
        except Exception as e:
            log.debug(f"Nessun ordine da cancellare o errore minore: {e}")

        # 2. Inviato ordine AGGRESSIVO (Limit alto = Market Buy)
        order_args = OrderArgs(token_id=token_id, price=price, size=config.BET_SIZE, side=BUY)
        
        log.info(f"🚀 Lancio ordine a MERCATO {label} (Limit aggressivo: {price} | Base: {base_price})")
        
        signed_order = client.create_order(order_args)
        resp = client.post_order(signed_order, OrderType.GTC)
        
        if resp.get("success"):
            log.info(f"✅ Ordine ESEGUITO (o in esecuzione immediata) | ID: {resp.get('orderID')}")
            return True
        else:
            log.error(f"❌ Errore esecuzione ordine: {resp.get('errorMsg')}")
            return False
            
    except Exception as e:
        log.error(f"Errore critico trader: {e}")
        return False
