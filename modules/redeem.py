import json
import os
import time
import requests
from web3 import Web3
from eth_account import Account
import config
from modules.logger import get_logger

log = get_logger("redeem")

# Indirizzi Polymarket (Polygon)
CTF_CONTRACT   = Web3.to_checksum_address("0x4D970805f78A966f121DC7FA03bcB21128F75C8c")
USDC_E         = Web3.to_checksum_address("0x2791bca1f2de4661ed88a30c99a7a9449aa84174")
USDC_NATIVE    = Web3.to_checksum_address("0x3c499c542cef5e3811e1192ce70d8cc03d5c3359")
RELAYER_URL    = "https://relayer-v2.polymarket.com"
DATA_API       = "https://data-api.polymarket.com"

RPC_URLS = ["https://1rpc.io/matic", "https://rpc.ankr.com/polygon", "https://polygon-rpc.com"]

# ABI minimale: redeemPositions su CTF Exchange
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

# ABI per ProxyWallet custom di Polymarket
PROXYWALLET_ABI = [
    {
        "name": "proxy",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [{"name": "calls", "type": "tuple[]", "components": [
            {"name": "typeCode", "type": "uint8"},
            {"name": "to",       "type": "address"},
            {"name": "value",    "type": "uint256"},
            {"name": "data",     "type": "bytes"}
        ]}],
        "outputs": [{"name": "returnValues", "type": "bytes[]"}]
    },
    {
        "name": "owner",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}]
    }
]

def load_trades_robust():
    """Carica trades.json gestendo corruzioni e diverse codifiche."""
    path = "data/trades.json"
    if not os.path.exists(path):
        return []
    for enc in ['utf-8', 'utf-8-sig', 'utf-16', 'cp1252']:
        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read().strip().replace('\x00', '')
                if not content:
                    return []
                return json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    log.error("File trades.json corrotto. Rinominato per ripartire.")
    try:
        os.rename(path, f"{path}.corrupt_{int(time.time())}")
    except Exception:
        pass
    return []

def save_trades_robust(trades):
    """Salva trades.json in modo sicuro."""
    path = "data/trades.json"
    try:
        with open(path, "w", encoding='utf-8') as f:
            json.dump(trades, f, indent=4)
    except Exception as e:
        log.error(f"Errore salvataggio trades.json: {e}")

def get_matic_balance(address: str) -> float | None:
    for rpc in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            return float(Web3.from_wei(w3.eth.get_balance(address), 'ether'))
        except Exception:
            continue
    return None

def get_redeemable_positions(proxy_address: str) -> list:
    """Recupera le posizioni riscattabili dal data-api di Polymarket."""
    url = f"{DATA_API}/positions?user={proxy_address}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                positions = data.get("Positions") or data.get("positions") or []
            elif isinstance(data, list):
                positions = data
            else:
                positions = []
            
            redeemable = []
            for p in positions:
                if p.get("redeemable"):
                    pnl = float(p.get("percentRealizedPnl", 0))
                    if pnl > -50:
                        redeemable.append(p)
                    else:
                        log.debug(f"Salto posizione persa (PNL {pnl}%): {p.get('title')}")
            
            log.info(f"Data API: {len(positions)} totali, {len(redeemable)} vincite reali da incassare.")
            return redeemable
    except Exception as e:
        log.debug(f"Errore lettura posizioni: {e}")
    return []

def _execute_redeem_proxywallet(w3, account, proxy_addr, cond_id, idx_sets, collateral_token=None) -> bool:
    """Invia redeemPositions al CTF tramite ProxyWallet.proxy()."""
    try:
        # Se non specificato, proviamo prima USDC Nativo (più comune ora) poi USDC.e
        tokens_to_try = [collateral_token] if collateral_token else [USDC_NATIVE, USDC_E]
        
        ctf = w3.eth.contract(address=CTF_CONTRACT, abi=CTF_ABI)
        parent_id = b'\x00' * 32
        if isinstance(cond_id, str):
            cond_id_bytes = bytes.fromhex(cond_id.replace("0x", ""))
        else:
            cond_id_bytes = cond_id

        pw = w3.eth.contract(address=proxy_addr, abi=PROXYWALLET_ABI)
        
        for token in tokens_to_try:
            log.debug(f"Tentativo redeem con collateral: {token}")
            redeem_data = ctf.encode_abi(
                abi_element_identifier="redeemPositions",
                args=[token, parent_id, cond_id_bytes, [int(i) for i in idx_sets]]
            )

            calls = [(1, CTF_CONTRACT, 0, bytes.fromhex(redeem_data.replace("0x", "")))]
            
            # Recupero nonce robusto
            current_nonce = w3.eth.get_transaction_count(account.address, 'pending')
            
            tx_params = {
                'from': account.address,
                'nonce': current_nonce,
                'gas': 600000,
                'gasPrice': w3.to_wei('250', 'gwei')
            }

            try:
                tx = pw.functions.proxy(calls).build_transaction(tx_params)
                signed_tx = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                log.info(f"⏳ Transazione inviata ({token[-6:]}) con nonce {current_nonce}... attendo conferma.")
                
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                if receipt.status == 1:
                    log.info(f"✅ Transazione confermata! TX: {tx_hash.hex()}")
                    return True
            except Exception as e:
                err_msg = str(e)
                if "nonce too low" in err_msg.lower() or "already known" in err_msg.lower():
                    # Prova a estrarre il nonce corretto dal messaggio di errore (es: "next nonce 30")
                    import re
                    match = re.search(r'next nonce (\d+)', err_msg)
                    if match:
                        correct_nonce = int(match.group(1))
                        log.warning(f"🔄 Nonce errato ({current_nonce}). Riprovo con nonce corretto: {correct_nonce}")
                        tx_params['nonce'] = correct_nonce
                        tx = pw.functions.proxy(calls).build_transaction(tx_params)
                        signed_tx = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                        if receipt.status == 1:
                            log.info(f"✅ Transazione confermata al secondo tentativo!")
                            return True
                log.warning(f"❌ Tentativo fallito per token {token}: {e}")
                
        return False

    except Exception as e:
        log.error(f"Errore _execute_redeem_proxywallet: {e}")
        return False

def get_relayer_nonce(address: str, wallet_type: str = "SAFE") -> str:
    """Recupera il nonce dal Relayer V2 per l'indirizzo del signer (EOA)."""
    try:
        url = f"{RELAYER_URL}/nonce?address={address}&type={wallet_type}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return str(resp.json().get("nonce", "0"))
    except Exception as e:
        log.error(f"Errore recupero nonce relayer ({wallet_type}): {e}")
    return "0"

def sign_relayer_submit(signer_account, to_addr, proxy_wallet, data_hex, nonce):
    """
    Firma la richiesta di submit per il Relayer V2 usando EIP-712 (SafeTx) in modo nativo.
    """
    from eth_account.messages import encode_typed_data
    from web3 import Web3
    
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
        "operation": 0,  # 0 = Call
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
        "operation": 0,          # INTERO
        "safeTxGas": "0",        # STRINGA
        "baseGas": "0",
        "gasToken": "0x0000000000000000000000000000000000000000",
        "refundReceiver": "0x0000000000000000000000000000000000000000"
    }

def _execute_redeem_relayer(cond_id: str, idx_sets: list, proxy_address: str, collateral_token=None) -> bool:
    """Invia il redeem tramite Relayer V2 di Polymarket con firma EIP-712 (Gasless)."""
    if not config.RELAYER_API_KEY or not config.RELAYER_API_KEY_ADDRESS:
        log.error("Relayer API Keys mancanti.")
        return False
        
    # Proviamo entrambi i token (Nativo e E) perché il Relayer è schizzinoso
    tokens_to_try = [collateral_token] if collateral_token else [USDC_NATIVE, USDC_E]
    
    # Il tipo di wallet: PROXY per i wallet standard Polymarket, SAFE per quelli Gnosis
    # La maggior parte dei nuovi utenti ha PROXY
    tx_types = ["PROXY", "SAFE"]
    
    signer = Account.from_key(config.PRIVATE_KEY)
    
    for token in tokens_to_try:
        for tx_type in tx_types:
            try:
                log.debug(f"Tentativo Relayer ({tx_type}) con token {token[-6:]}...")
                w3_temp = Web3(Web3.HTTPProvider(RPC_URLS[0]))
                ctf = w3_temp.eth.contract(address=CTF_CONTRACT, abi=CTF_ABI)
                parent_id = b'\x00' * 32
                
                if isinstance(cond_id, str):
                    cond_id_bytes = bytes.fromhex(cond_id.replace("0x", ""))
                else:
                    cond_id_bytes = cond_id

                data_hex = ctf.encode_abi(
                    abi_element_identifier="redeemPositions",
                    args=[token, parent_id, cond_id_bytes, [int(i) for i in idx_sets]]
                )
                
                # Chiediamo il nonce specifico per il tipo di wallet
                rel_nonce = get_relayer_nonce(signer.address, tx_type)
                
                signature, sig_params = sign_relayer_submit(
                    signer, CTF_CONTRACT, proxy_address, data_hex, rel_nonce
                )

                headers = {
                    "Content-Type": "application/json",
                    "RELAYER_API_KEY": config.RELAYER_API_KEY,
                    "RELAYER_API_KEY_ADDRESS": config.RELAYER_API_KEY_ADDRESS,
                }
                
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
                
                # Se è SAFE, aggiungiamo i parametri della firma EIP-712
                if tx_type == "SAFE":
                    body["signature_params"] = sig_params

                resp = requests.post(f"{RELAYER_URL}/submit", json=body, headers=headers, timeout=15)
                
                if resp.status_code in (200, 201):
                    log.info(f"✅ Redeem accettato dal RELAYER ({tx_type})! ID: {resp.json().get('transactionID')}")
                    return True
                elif resp.status_code == 502:
                    log.debug("Relayer temporaneamente offline (502 Bad Gateway).")
                    return False
                else:
                    log.debug(f"Relayer ha rifiutato {tx_type}/{token[-6:]} ({resp.status_code}): {resp.text[:200]}")
                    continue

            except Exception as e:
                log.debug(f"Errore tentativo Relayer {tx_type}: {e}")
                continue
                
    return False

def sync_external_winnings():
    """Ricerca e incassa tutte le posizioni 'redeemable' del portafoglio (SOLO RELAYER)."""
    if not config.POLY_PROXY_ADDRESS:
        return

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

        if not cond_id:
            continue

        if idx is not None:
            idx_sets = [1 << int(idx)]
        else:
            idx_sets = [1, 2]

        log.info(f"⚡ Incasso Gasless: {title} | conditionId: {cond_id}")

        success = _execute_redeem_relayer(cond_id, idx_sets, proxy_addr)
            
        if success:
            log.info(f"✅ Claim completato via Relayer per: {title}")
        else:
            log.warning(f"⏳ Relayer non disponibile per: {title}. Riproverò.")

        time.sleep(2)

def check_winnings(proxy_address: str) -> float:
    """Controlla le vincite stimate in base ai trade locali (solo recenti)."""
    trades = load_trades_robust()
    if not trades:
        return 0.0
    total = 0.0
    now = time.time()
    try:
        updated = False
        # Controlliamo solo i trade degli ultimi 60 minuti per evitare blocchi
        for t in trades:
            # Se il trade è più vecchio di 1 ora e ancora pending, lo saltiamo per ora
            if t.get("status") == "pending" and (now - t.get("timestamp", 0)) > 3600:
                continue

            if t.get("status") == "pending" or t.get("status") == "resolved_unverified":
                # Aspettiamo almeno 5 minuti dal trade prima di controllare l'esito
                if (now - t.get("timestamp", 0)) < 300:
                    continue
                
                resp = requests.get(
                    f"{config.GAMMA_URL}/markets",
                    params={"conditionId": t["conditionId"]},
                    timeout=5
                )
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
                            log.info(f"🏆 VITTORIA! Mercato {t.get('slug')} risolto a nostro favore!")
                        else:
                            t["status"] = "lost"
                            log.info(f"❌ SCONFITTA. Mercato {t.get('slug')} perso.")
                    else:
                        t["status"] = "resolved"
                        log.info(f"🏆 Mercato {t.get('slug')} risolto (esito incerto).")
                        
                    updated = True
            
            # Conta tutte le posizioni che devono ancora essere incassate
            if t.get("status") in ["resolved", "claiming"]:
                total += config.BET_SIZE * 2
                
        if updated:
            save_trades_robust(trades)
    except Exception as e:
        log.error(f"Errore check_winnings: {e}")
    return total

def auto_redeem():
    """Tenta l'incasso automatico sui mercati risolti registrati localmente (SOLO RELAYER)."""
    if not config.POLY_PROXY_ADDRESS or not config.PRIVATE_KEY:
        return
    trades = load_trades_robust()
    if not trades:
        return

    proxy_addr = Web3.to_checksum_address(config.POLY_PROXY_ADDRESS)
    updated = False

    for t in [tr for tr in trades if tr.get("status") in ["resolved", "claiming"]]:
        log.info(f"⚡ Auto-redeem Gasless per {t.get('slug')}...")
        idx_sets = [1] if t.get("action") == "BUY_UP" else [2]

        t["status"] = "claiming" 
        t["redeem_attempts"] = t.get("redeem_attempts", 0) + 1
        save_trades_robust(trades)

        # Tentativo SOLO via Relayer (Gasless)
        success = _execute_redeem_relayer(t["conditionId"], idx_sets, proxy_addr)
        
        if success:
            log.info(f"✅ Auto-redeem completato via Relayer per {t.get('slug')}")
            t["status"] = "claimed"
            updated = True
        else:
            log.warning(f"⏳ Relayer non disponibile o errore per {t.get('slug')}. Riproverò.")
            # Se dopo 10 tentativi fallisce ancora, lo segnamo come failed per non bloccare il bot
            if t.get("redeem_attempts", 0) >= 10:
                t["status"] = "failed"
            updated = True

    if updated:
        save_trades_robust(trades)
