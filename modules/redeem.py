import json
import os
import time
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
import config
from modules.logger import get_logger

log = get_logger("redeem")

CTF_CONTRACT   = Web3.to_checksum_address("0x4D970805f78A966f121DC7FA03bcB21128F75C8c")
USDC_E         = Web3.to_checksum_address("0x2791bca1f2de4661ed88a30c99a7a9449aa84174")
USDC_NATIVE    = Web3.to_checksum_address("0x3c499c542cef5e3811e1192ce70d8cc03d5c3359")
RELAYER_URL    = "https://relayer-v2.polymarket.com"
DATA_API       = "https://data-api.polymarket.com"

RPC_URLS = ["https://1rpc.io/matic", "https://rpc.ankr.com/polygon", "https://polygon-rpc.com"]

CTF_ABI = [
    {
        "name": "redeemPositions",
        "type": "function",
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSets", "type": "uint256[]"}
        ],
        "outputs": []
    }
]

def load_trades_robust():
    path = "data/trades.json"
    if not os.path.exists(path): return []
    for enc in ['utf-8', 'utf-8-sig', 'utf-16', 'cp1252']:
        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read().strip().replace('\x00', '')
                if not content: return []
                return json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    log.error("File trades.json corrotto. Rinominato.")
    try:
        os.rename(path, f"{path}.corrupt_{int(time.time())}")
    except Exception:
        pass
    return []

def save_trades_robust(trades):
    path = "data/trades.json"
    try:
        with open(path, "w", encoding='utf-8') as f:
            json.dump(trades, f, indent=4)
    except Exception as e:
        log.error(f"Errore salvataggio: {e}")

def get_redeemable_positions(proxy_address: str) -> list:
    url = f"{DATA_API}/positions?user={proxy_address}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                positions = data
            else:
                positions = data.get("Positions") or data.get("positions") or []
            return [p for p in positions if p.get("redeemable")]
    except Exception as e:
        log.debug(f"Errore lettura posizioni: {e}")
    return []

def get_matic_balance(address: str) -> float | None:
    for rpc in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            return float(Web3.from_wei(w3.eth.get_balance(address), 'ether'))
        except Exception:
            continue
    return None

def get_relayer_nonce(address: str, wallet_type: str = "SAFE") -> str:
    try:
        url = f"{RELAYER_URL}/nonce?address={address}&type={wallet_type}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return str(resp.json().get("nonce", "0"))
    except Exception as e:
        log.error(f"Errore recupero nonce relayer ({wallet_type}): {e}")
    return "0"

def sign_relayer_submit(signer_account, to_addr, proxy_wallet, data_hex, nonce):
    domain = {
        "chainId": 137,
        "verifyingContract": Web3.to_checksum_address(proxy_wallet)
    }
    types = {
        "SafeTx": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "operation", "type": "uint8"},
            {"name": "safeTxGas", "type": "uint256"},
            {"name": "baseGas", "type": "uint256"},
            {"name": "gasPrice", "type": "uint256"},
            {"name": "gasToken", "type": "address"},
            {"name": "refundReceiver", "type": "address"},
            {"name": "nonce", "type": "uint256"}
        ]
    }
    message = {
        "to": Web3.to_checksum_address(to_addr),
        "value": 0,
        "data": bytes.fromhex(data_hex.replace("0x", "")),
        "operation": 0,
        "safeTxGas": 0,
        "baseGas": 0,
        "gasPrice": 0,
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000",
        "nonce": int(nonce)
    }
    
    signable_msg = encode_typed_data(domain_data=domain, message_types=types, message_data=message)
    signed_msg = signer_account.sign_message(signable_msg)
    
    return "0x" + signed_msg.signature.hex(), {
        "gasPrice": "0",
        "operation": 0,
        "safeTxGas": "0",
        "baseGas": "0",
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000"
    }

def _execute_redeem_relayer(cond_id: str, idx_sets: list, proxy_address: str, collateral_token=None) -> bool:
    if not config.RELAYER_API_KEY or not config.RELAYER_API_KEY_ADDRESS:
        log.error("Relayer API Keys mancanti.")
        return False
        
    tokens_to_try = [collateral_token] if collateral_token else [USDC_NATIVE, USDC_E]
    tx_types = ["SAFE", "PROXY"]
    
    try:
        signer = Account.from_key(config.PRIVATE_KEY)
    except Exception as e:
        log.error(f"Errore caricamento Private Key: {e}")
        return False
    
    for token in tokens_to_try:
        for tx_type in tx_types:
            try:
                log.debug(f"Tentativo Relayer ({tx_type}) con token {token[-6:]}...")
                w3_temp = Web3()
                ctf = w3_temp.eth.contract(address=CTF_CONTRACT, abi=CTF_ABI)
                parent_id = b'\x00' * 32
                
                cond_id_bytes = bytes.fromhex(cond_id.replace("0x", "")) if isinstance(cond_id, str) else cond_id
                data_hex = ctf.encode_abi(
                    abi_element_identifier="redeemPositions",
                    args=[token, parent_id, cond_id_bytes, [int(i) for i in idx_sets]]
                )
                
                rel_nonce = get_relayer_nonce(signer.address, tx_type)
                
                if tx_type == "SAFE":
                    signature, sig_params = sign_relayer_submit(
                        signer, CTF_CONTRACT, proxy_address, data_hex, rel_nonce
                    )
                else:
                    signature, _ = sign_relayer_submit(
                        signer, CTF_CONTRACT, proxy_address, data_hex, rel_nonce
                    )
                    sig_params = None

                # Crucial Fix: Standard Headers matching the polymarket webapp
                # Authentication for relayer could require matching the web interface headers
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": str(config.RELAYER_API_KEY).strip(),
                }

                # In many Polymarket integrations, the relayer requires the standard Polymarket Clob API headers
                if config.POLY_API_KEY:
                    headers["poly-api-key"] = str(config.POLY_API_KEY).strip()
                if hasattr(config, 'RELAYER_API_KEY_ADDRESS') and config.RELAYER_API_KEY_ADDRESS:
                    headers["poly-relayer-api-key-address"] = str(config.RELAYER_API_KEY_ADDRESS).strip()

                # Non logghiamo la chiave intera, ma verifichiamo che ci sia
                key_preview = str(config.RELAYER_API_KEY).strip()[:5] + "..." if config.RELAYER_API_KEY else "None"
                # log.debug(f"Headers inviati al relayer: poly-relayer-api-key={key_preview}")

                body = {
                    "type": tx_type,
                    "from": signer.address,
                    "to": CTF_CONTRACT,
                    "proxyWallet": proxy_address,
                    "data": data_hex,
                    "value": "0",
                    "nonce": str(rel_nonce),
                    "signature": signature
                }
                
                if tx_type == "SAFE" and sig_params:
                    body["signature_params"] = sig_params

                resp = requests.post(f"{RELAYER_URL}/submit", json=body, headers=headers, timeout=20)
                
                if resp.status_code == 429:
                    log.warning(f"Rate limit (429) dal relayer per {tx_type}. Pausa di 5 secondi...")
                    time.sleep(5)
                    # riprova 1 volta in caso di 429
                    resp = requests.post(f"{RELAYER_URL}/submit", json=body, headers=headers, timeout=20)

                if resp.status_code in (200, 201):
                    log.info(f"✅ Redeem gasless accettato ({tx_type})! ID: {resp.json().get('transactionID')}")
                    return True
                elif resp.status_code == 502:
                    log.debug("Relayer 502 Bad Gateway (probabilmente errore Payload/Network su Polymarket).")
                else:
                    log.debug(f"Relayer ha rifiutato {tx_type}/{token[-6:]} ({resp.status_code}): {resp.text[:200]}")
                    if resp.status_code == 401:
                        # Log the body to inspect what could be triggering the 401
                        # Since API keys are fine for GET /nonce, it's likely the signature or the API keys for POST /submit
                        log.debug(f"Dettagli 401 per {tx_type}: poly-relayer-api-key usato: {headers['poly-relayer-api-key'][:5]}...")

                    
            except Exception as e:
                log.debug(f"Errore tentativo Relayer {tx_type}: {e}")
                continue

            # Anti-rate limit: un po' di respiro tra un tentativo e l'altro
            time.sleep(2.5)
                
    return False


def sync_external_winnings():
    if not config.POLY_PROXY_ADDRESS: return
    proxy_addr = Web3.to_checksum_address(config.POLY_PROXY_ADDRESS)
    log.info(f"🔍 Controllo posizioni riscattabili per: {proxy_addr}...")

    positions = get_redeemable_positions(proxy_addr)
    if not positions:
        log.debug("Nessuna posizione riscattabile trovata.")
        return

    log.info(f"🎯 Trovate {len(positions)} posizione/i riscattabili.")
    for p in positions:
        cond_id = p.get("conditionId") or p.get("condition_id")
        title   = p.get("title") or p.get("market", "Unknown Market")
        idx     = p.get("outcomeIndex")

        if not cond_id: continue
        idx_sets = [1 << int(idx)] if idx is not None else [1, 2]

        log.info(f"⚡ Incasso Gasless: {title} | conditionId: {cond_id}")
        success = _execute_redeem_relayer(cond_id, idx_sets, proxy_addr)
            
        if success:
            log.info(f"✅ Claim completato via Relayer per: {title}")
        else:
            log.warning(f"⏳ Relayer fallito per: {title}. Riproverò al prossimo giro.")
        time.sleep(2)

def check_winnings(proxy_address: str) -> float:
    trades = load_trades_robust()
    if not trades: return 0.0
    total = 0.0
    now = time.time()
    try:
        updated = False
        for t in trades:
            if t.get("status") == "pending" and (now - t.get("timestamp", 0)) > 3600:
                continue

            if t.get("status") in ("pending", "resolved_unverified"):
                if (now - t.get("timestamp", 0)) < 300:
                    continue
                
                resp = requests.get(f"{config.GAMMA_URL}/markets", params={"conditionId": t["conditionId"]}, timeout=5)
                data = resp.json()
                if data and isinstance(data, list) and data[0].get("resolved"):
                    m = data[0]
                    outcomes = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes"), str) else m.get("outcomes")
                    prices = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices")
                    
                    if outcomes and prices:
                        up_idx = next((i for i, o in enumerate(outcomes) if "up" in str(o).lower()), 0)
                        down_idx = 1 - up_idx
                        target_idx = up_idx if t.get("action") == "BUY_UP" else down_idx
                        
                        if float(prices[target_idx]) == 1.0:
                            t["status"] = "resolved"
                            log.info(f"🏆 VITTORIA! {t.get('slug')}")
                        else:
                            t["status"] = "lost"
                            log.info(f"❌ SCONFITTA. {t.get('slug')}")
                    else:
                        t["status"] = "resolved"
                        log.info(f"🏆 Mercato {t.get('slug')} risolto.")
                    updated = True
            
            if t.get("status") in ("resolved", "claiming"):
                total += config.BET_SIZE * 2
                
        if updated:
            save_trades_robust(trades)
    except Exception as e:
        log.error(f"Errore check_winnings: {e}")
    return total

def auto_redeem():
    if not config.POLY_PROXY_ADDRESS or not config.PRIVATE_KEY: return
    trades = load_trades_robust()
    if not trades: return

    proxy_addr = Web3.to_checksum_address(config.POLY_PROXY_ADDRESS)
    updated = False

    for t in [tr for tr in trades if tr.get("status") in ("resolved", "claiming")]:
        log.info(f"⚡ Auto-redeem Gasless per {t.get('slug')}...")
        idx_sets = [1] if t.get("action") == "BUY_UP" else [2]

        t["status"] = "claiming" 
        t["redeem_attempts"] = t.get("redeem_attempts", 0) + 1
        save_trades_robust(trades)

        success = _execute_redeem_relayer(t["conditionId"], idx_sets, proxy_addr)
        
        if success:
            log.info(f"✅ Auto-redeem completato via Relayer per {t.get('slug')}")
            t["status"] = "claimed"
            updated = True
        else:
            log.warning(f"⏳ Relayer fallito per {t.get('slug')}.")
            if t.get("redeem_attempts", 0) >= 10:
                t["status"] = "failed"
            updated = True

    if updated:
        save_trades_robust(trades)
