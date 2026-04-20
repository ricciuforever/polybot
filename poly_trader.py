import os
import json
import logging
from web3 import Web3
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from eth_account import Account
import requests
import re
import config
from modules.http_utils import apply_ip_binding
apply_ip_binding()
import traceback
from modules.logger import get_logger

log = get_logger("poly_trader")

class PolyTrader:
    """Gestisce il trading on-chain su Polymarket tramite CLOB API."""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config.POLY_RPC))
        self.account = Account.from_key(config.PRIVATE_KEY)
        self.my_address = self.account.address
        self.state_path = "data/checked_conditions.json"
        self.checked_conditions = self._load_checked_conditions()
        
        # 1. Client CLOB
        self.client = ClobClient(
            host=config.POLY_CLOB_URL,
            key=config.PRIVATE_KEY,
            chain_id=137
        )
        
        # 2. Autenticazione L2
        try:
            log.info("🔐 Autenticazione L2...")
            try:
                creds = self.client.derive_api_key()
                self.client.set_api_creds(creds)
                log.info("✅ Credenziali DERIVATE.")
            except:
                creds = self.client.create_api_key()
                self.client.set_api_creds(creds)
                log.info("✅ Credenziali CREATE.")
        except Exception as e:
            log.error(f"Errore Auth L2: {e}")

        # 3. Approval USDC.e
        self.ensure_allowance()

        # ABIs
        self.usdc_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}, {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"}]
        self.safe_abi = [
            {"inputs": [], "name": "nonce", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [
                {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "data", "type": "bytes"},
                {"name": "operation", "type": "uint8"}, {"name": "safeTxGas", "type": "uint256"}, {"name": "baseGas", "type": "uint256"},
                {"name": "gasPrice", "type": "uint256"}, {"name": "gasToken", "type": "address"}, {"name": "refundReceiver", "type": "address"},
                {"name": "signatures", "type": "bytes"}
            ], "name": "execTransaction", "outputs": [{"name": "success", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}
        ]
        self.redeem_abi = [
            {"inputs": [{"name": "collateralToken", "type": "address"}, {"name": "parentCollectionId", "type": "bytes32"}, {"name": "conditionId", "type": "bytes32"}, {"name": "indexSets", "type": "uint256[]"}], "name": "redeemPositions", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"name": "", "type": "bytes32"}, {"name": "", "type": "uint256"}], "name": "payoutNumerators", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "owner", "type": "address"}, {"name": "id", "type": "uint256"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "parentCollectionId", "type": "bytes32"}, {"name": "conditionId", "type": "bytes32"}, {"name": "indexSet", "type": "uint256"}], "name": "getCollectionId", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"}
        ]
        
        # Contratti
        self.usdc_contract = self.w3.eth.contract(address=Web3.to_checksum_address(config.POLY_USDC), abi=self.usdc_abi)
        self.ctf_contract = self.w3.eth.contract(address=Web3.to_checksum_address(config.POLY_CTF), abi=self.redeem_abi)
        if config.SAFE_ADDRESS:
            self.safe_contract = self.w3.eth.contract(address=Web3.to_checksum_address(config.SAFE_ADDRESS), abi=self.safe_abi)
        else:
            self.safe_contract = None

    def ensure_allowance(self):
        try:
            abi_allowance = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"}]
            c = self.w3.eth.contract(address=Web3.to_checksum_address(config.POLY_USDC), abi=abi_allowance)
            allowance = c.functions.allowance(self.my_address, config.POLY_EXCHANGE).call()
            if allowance < 1_000_000: # 1 USDC
                abi_app = [{"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"}]
                c_app = self.w3.eth.contract(address=Web3.to_checksum_address(config.POLY_USDC), abi=abi_app)
                tx = c_app.functions.approve(config.POLY_EXCHANGE, 2**256-1).build_transaction({
                    'from': self.my_address, 'nonce': self.w3.eth.get_transaction_count(self.my_address),
                    'gas': 100000, 'gasPrice': self.w3.eth.gas_price
                })
                signed = self.w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
                self.w3.eth.send_raw_transaction(signed.raw_transaction)
                log.info("🔓 Inviato sblocco USDC.e")
        except Exception as e:
            log.warning(f"Errore durante l'invio dello sblocco USDC.e: {e}")

    def get_balances(self):
        """Recupera il saldo totale USDC (Metamask + Safe) e POL."""
        try:
            # Saldo POL (Gas) - solo Metamask
            pol = self.w3.eth.get_balance(self.my_address)
            
            # Saldo USDC on Metamask
            usdc_eoa = self.usdc_contract.functions.balanceOf(self.my_address).call()
            
            # Saldo USDC on Safe (se presente)
            usdc_safe = 0
            if config.SAFE_ADDRESS:
                usdc_safe = self.usdc_contract.functions.balanceOf(Web3.to_checksum_address(config.SAFE_ADDRESS)).call()
            
            total_usdc = usdc_eoa + usdc_safe
            return float(self.w3.from_wei(pol, 'ether')), float(total_usdc) / 1_000_000
        except Exception as e:
            log.debug(f"⚠️ Errore lettura saldi (probabile 429): {e}")
            return None, None # Restituisce None per indicare errore di lettura anziché saldo 0

    def _load_checked_conditions(self):
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, "r") as f:
                    return set(json.load(f))
        except Exception as e:
            log.debug(f"Nessuno stato caricato o errore lettura: {e}")
        return set()

    def _save_checked_conditions(self):
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, "w") as f:
                json.dump(list(self.checked_conditions), f)
        except Exception as e:
            log.error(f"Errore salvataggio stati: {e}")

    def execute_market_trade(self, token_id: str, amount_usdc: float, side: str = "BUY"):
        try:
            ob = self.client.get_order_book(token_id)
            if side == "BUY":
                best_price = float(ob.asks[0].price) if ob.asks else 0.99
            else:
                best_price = float(ob.bids[0].price) if ob.bids else 0.01

            # Garantiamo valore > 1.05$
            size = round((1.10 / best_price) + 0.1, 2)
            
            # Creazione Argomenti Ordine
            order_args = OrderArgs(price=best_price, size=size, side=side, token_id=token_id)
            
            # Se abbiamo un Builder ID, lo associamo all'ordine per tracciamento/commissioni
            if config.POLY_BUILDER_ID:
                order_args.builder_id = config.POLY_BUILDER_ID
                
            signed = self.client.create_order(order_args)
            resp = self.client.post_order(signed)
            
            if resp.get('success') or resp.get('orderID'):
                oid = resp.get('orderID') or resp.get('order_id')
                return True, oid
            return False, str(resp)
        except Exception as e:
            error_msg = str(e)
            # Gestione Dinamica Allowance: se l'errore ci dice l'indirizzo dello spender mancante, lo approviamo!
            if "allowance" in error_msg.lower() and "spender:" in error_msg.lower():
                try:
                    import re
                    spender = re.search(r"spender: (0x[a-fA-F0-9]{40})", error_msg).group(1)
                    log.info(f"🛡️ Rilevato nuovo spender: {spender}. Invio APPROVAL automatica...")
                    self.approve_spender(spender)
                    return False, "Allowance richiesta. Riprova tra 10 secondi."
                except Exception as ex:
                    log.error(f"Errore durante l'approvazione automatica spender (execute_market_trade): {ex}")
            return False, error_msg

    def sniper_trade(self, market: dict, target_side: str, limit_price: float = 0.85) -> bool:
        """Metodo principale per la strategia Sniper: traduce il mercato in un ordine CLOB."""
        try:
            # Determina direzione
            if target_side == "UP":
                token_id = market['token_yes']
                direction = "UP → BUY YES"
            else:
                token_id = market['token_no']
                direction = "DOWN → BUY NO"
            
            # Verifica saldo PRIMA di piazzare
            _, usdc_balance = self.get_balances()
            min_bet = 1.05  # Minimo CLOB
            
            if usdc_balance < min_bet:
                log.error(f"   ❌ Saldo insufficiente: ${usdc_balance:.2f} (minimo ${min_bet})")
                return False
            
            # Adatta bet_size al saldo disponibile
            bet_size = min(config.BET_SIZE, usdc_balance * 0.95)  # Usa 95% del saldo
            bet_size = max(bet_size, min_bet)  # Mai sotto il minimo
            
            log.info(f"   📋 Direzione: {direction}")
            log.info(f"   📋 Token ID: {token_id[:20]}...")
            log.info(f"   📋 Saldo: ${usdc_balance:.2f} | Importo: ${bet_size:.2f}")
            
            # Usiamo il Limit Price ESATTO richiesto (nessun rialzo per spread)
            buy_price = round(limit_price, 2)
            
            # Calcolo size basato sul prezzo limite esatto configurato
            size = round(bet_size / buy_price, 2)
            
            log.info(f"   📋 Size stimata: {size} shares | Prezzo ASSOLUTO limite: ${buy_price} (Limit Fill)")
            
            from py_clob_client.clob_types import OrderArgs
            order_args = OrderArgs(
                price=buy_price,
                size=size,
                side="BUY",
                token_id=token_id
            )
            
            log.info(f"   📋 Firma ordine in corso...")
            signed = self.client.create_order(order_args)
            
            log.info(f"   📋 Invio ordine al CLOB...")
            
            # --- Retry Logic per 425 Service Not Ready ---
            max_retries = 3
            resp = {}
            for attempt in range(max_retries):
                try:
                    resp = self.client.post_order(signed)
                    break
                except Exception as api_e:
                    if "425" in str(api_e) or "not ready" in str(api_e).lower():
                        if attempt < max_retries - 1:
                            import time
                            log.warning(f"   ⚠️ Polymarket non pronto (425). Ritento in 2s... ({attempt+1}/{max_retries})")
                            time.sleep(2)
                            continue
                    raise api_e # Rilancia se non è 425 o abbiamo finito i retries
            # ---------------------------------------------
            
            log.info(f"   📋 Risposta CLOB: {resp}")
            
            if resp.get('success') or resp.get('orderID'):
                oid = resp.get('orderID') or resp.get('order_id')
                log.info(f"   ✅ Ordine piazzato! ID: {oid}")
                return True
            else:
                log.error(f"   ❌ Ordine RIFIUTATO dal CLOB: {resp}")
                return False
                
        except Exception as e:
            log.error(f"   ❌ ERRORE TRADE: {e}")
            # Gestione Allowance automatica
            error_msg = str(e)
            if "allowance" in error_msg.lower():
                log.info(f"   🛡️ Problema di allowance rilevato, provo ad approvare...")
                try:
                    spender = re.search(r"spender: (0x[a-fA-F0-9]{40})", error_msg).group(1)
                    self.approve_spender(spender)
                except Exception as ex:
                    log.error(f"Errore durante l'approvazione automatica spender (sniper_trade): {ex}")
            return False

    def approve_spender(self, spender_address: str):
        """Approva un indirizzo specifico (contratto di scambio) a spendere USDC.e."""
        try:
            abi_app = [{"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"}]
            c_app = self.w3.eth.contract(address=Web3.to_checksum_address(config.POLY_USDC), abi=abi_app)
            tx = c_app.functions.approve(Web3.to_checksum_address(spender_address), 2**256-1).build_transaction({
                'from': self.my_address, 'nonce': self.w3.eth.get_transaction_count(self.my_address),
                'gas': 100000, 'gasPrice': self.w3.eth.gas_price
            })
            signed = self.w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
            self.w3.eth.send_raw_transaction(signed.raw_transaction)
            log.info(f"✅ Approvato spender {spender_address}")
        except Exception as e:
            log.error(f"Errore approvazione dinamica: {e}")

    def auto_redeem(self):
        """Riscuote i profitti scansionando Posizioni Attive + Activity History (per trade manuali)."""
        try:
            target_address = config.SAFE_ADDRESS if config.SAFE_ADDRESS else self.my_address
            redeemed = 0
            seen_conditions = set()
            
            # --- 1. Raccolta Condition ID da Scansionare ---
            potential_conditions = []
            
            addresses_to_check = [self.my_address]
            if config.SAFE_ADDRESS and config.SAFE_ADDRESS.lower() != self.my_address.lower():
                addresses_to_check.append(config.SAFE_ADDRESS)

            for addr in addresses_to_check:
                # A. Dalle Posizioni Attive (API)
                try:
                    pos_url = f"https://data-api.polymarket.com/positions?user={addr}"
                    pos_resp = requests.get(pos_url, timeout=10).json()
                    log.debug(f"      Check API {addr[:10]}... trovate {len(pos_resp)} posizioni.")
                    for p in pos_resp:
                        cid = p.get('conditionId') or p.get('condition_id')
                        # Filtro Rilassato: Proviamo a riscattare tutto ciò che ha una size minima.
                        if float(p.get('size', 0)) > 0.01 and cid:
                            if cid not in potential_conditions:
                                potential_conditions.append(cid)
                except Exception as e:
                    log.debug(f"      Errore fetch API per {addr[:10]}: {e}")
            
            # B. Dalla Cronologia Locale (Backup)
            try:
                if os.path.exists("trades_history.json"):
                    with open("trades_history.json", "r") as f:
                        hist_data = json.load(f)
                        added_h = 0
                        for trade in hist_data:
                            cid = trade.get('condition_id')
                            if cid and cid not in potential_conditions:
                                potential_conditions.append(cid)
                                added_h += 1
                        if added_h > 0:
                            log.info(f"   ↳ 📚 Aggiunti {added_h} ID dalla cronologia locale.")
            except Exception as e:
                log.warning(f"   ↳ ⚠️ Errore lettura storico: {e}")
            

            # Pre-filtro: Rimuoviamo quelli già verificati per non inquinare la lista
            potential_conditions = [c for c in potential_conditions if c not in self.checked_conditions]
            
            # Limite: Controlla solo i primi 50 (i più recenti)
            MAX_LIMIT = 50
            if len(potential_conditions) > MAX_LIMIT:
                potential_conditions = potential_conditions[:MAX_LIMIT]

            if not potential_conditions:
                log.info("   ↳ ℹ️ Nessuna scommessa pendente da verificare.")
                return 0

            usdc_token = Web3.to_checksum_address(config.POLY_USDC)
            parent = b'\x00' * 32

            log.info(f"   ↳ 🔎 Verifica on-chain di {len(potential_conditions)} mercati...")
            
            count = 0
            for cond_id in potential_conditions:
                if cond_id in self.checked_conditions: continue
                
                count += 1
                if count % 20 == 0:
                    log.info(f"      ... verificati {count}/{len(potential_conditions)} mercati")
                
                try:
                    # --- CONTROLLO ON-CHAIN RISOLUZIONE ---
                    try:
                        p0 = self.ctf_contract.functions.payoutNumerators(cond_id, 0).call()
                        p1 = self.ctf_contract.functions.payoutNumerators(cond_id, 1).call()
                        is_resolved = (p0 > 0 or p1 > 0)
                    except Exception as e:
                        if "429" in str(e):
                            log.warning("      ⚠️ Rate limit RPC (429). Pausa di 2 secondi...")
                            import time
                            time.sleep(2)
                        continue

                    if not is_resolved:
                        continue 
                    
                    # --- CONTROLLO BILANCIO ---
                    found_balance = 0
                    active_index = 0
                    active_address = None
                    
                    for idx in [1, 2]:
                        payout = p0 if idx == 1 else p1
                        if payout == 0: continue
                        
                        coll_id = self.ctf_contract.functions.getCollectionId(parent, cond_id, idx).call()
                        token_id = int(Web3.keccak(hexstr=usdc_token[2:].lower() + coll_id.hex()).hex(), 16)
                        
                        for test_addr in addresses_to_check:
                            bal = self.ctf_contract.functions.balanceOf(Web3.to_checksum_address(test_addr), token_id).call()
                            if bal > 0:
                                found_balance, active_index, active_address = bal, idx, test_addr
                                break
                        if found_balance > 0: break
                    
                    if found_balance == 0:
                        self.checked_conditions.add(cond_id)
                        continue

                    log.info(f"   ↳ 🎯 TROVATO! {found_balance/1e6} token vincenti su {active_address[:10]}...")

                    cond_bytes = bytes.fromhex(cond_id[2:] if cond_id.startswith("0x") else cond_id)
                    
                    # Generazione redeem_data compatibile con Web3 v7
                    try:
                        dummy_tx = self.ctf_contract.functions.redeemPositions(
                            usdc_token, parent, cond_bytes, [1, 2]
                        ).build_transaction({
                            'from': self.my_address, 'nonce': 0, 'gas': 1, 'gasPrice': 1
                        })
                        redeem_data = dummy_tx['data']
                    except Exception as e:
                        log.error(f"      ↳ Errore encoding transazione: {e}")
                        continue

                    # 1. Tentativo Relayer (Gasless)
                    if config.POLY_RELAYER_KEY:
                        log.info(f"   ↳ ⚡ Invio richiesta al Relayer Polymarket (Gasless)...")
                        # Endpoint aggiornato per v2/builder
                        relayer_url = "https://relayer-v2.polymarket.com/"
                        headers = {
                            "RELAYER_API_KEY": config.POLY_RELAYER_KEY,
                            "RELAYER_API_KEY_ADDRESS": config.POLY_RELAYER_ADDRESS,
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "method": "redeem",
                            "params": {
                                "conditionId": cond_id,
                                "collateralToken": usdc_token,
                                "parentCollectionId": "0x0000000000000000000000000000000000000000000000000000000000000000",
                                "indexSets": [1, 2]
                            }
                        }
                        
                        try:
                            relayer_resp = requests.post(relayer_url, json=payload, headers=headers, timeout=15)
                            log.info(f"   ↳ ⚡ Risposta Relayer: {relayer_resp.status_code}")
                            
                            if relayer_resp.status_code in [200, 201, 202]:
                                log.info(f"   ↳ 💰 ✅ Riscatto Gasless inoltrato!")
                                redeemed += 1
                                continue
                        except Exception as e:
                            log.warning(f"   ↳ ⚠️ Fallimento chiamata Relayer: {e}")

                    # --- FALLBACK: LOGICA SAFE PROXY o MANUALE ---
                    if config.SAFE_ADDRESS and active_address.lower() == config.SAFE_ADDRESS.lower() and self.safe_contract:
                        signature = "0x" + "000000000000000000000000" + self.my_address[2:].lower() + \
                                    "0000000000000000000000000000000000000000000000000000000000000000" + "01"
                        
                        tx = self.safe_contract.functions.execTransaction(
                            Web3.to_checksum_address(config.POLY_CTF), 0, redeem_data, 0, 0, 0, 0,
                            "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000",
                            Web3.to_bytes(hexstr=signature)
                        ).build_transaction({
                            'from': self.my_address,
                            'nonce': self.w3.eth.get_transaction_count(self.my_address),
                            'gas': 450000,
                            'gasPrice': int(self.w3.eth.gas_price * 1.3)
                        })
                        log.info(f"   ↳ 🛡️ Invio via SAFE Proxy (pagando gas in POL)...")
                    else:
                        tx = self.ctf_contract.functions.redeemPositions(
                            usdc_token, parent, cond_bytes, [1, 2]
                        ).build_transaction({
                            'from': self.my_address,
                            'nonce': self.w3.eth.get_transaction_count(self.my_address),
                            'gas': 250000,
                            'gasPrice': int(self.w3.eth.gas_price * 1.3)
                        })
                    
                    signed_tx = self.w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=35)
                    
                    if receipt.status == 1:
                        log.info(f"   ↳ 💰 ✅ Riscatto completato! TX: {tx_hash.hex()[:15]}...")
                        redeemed += 1
                    else:
                        log.warning(f"   ↳ 💰 ❌ Errore nella transazione di riscatto.")

                except Exception as e:
                    log.error(f"   ↳ ❌ Errore per {cond_id}: {e}")
            
            # Salva gli ID verificati per il prossimo avvio
            self._save_checked_conditions()
            
            # --- 3. AUTO-WITHDRAW (Sposta da Safe a Metamask) ---
            if redeemed > 0 or True: # Controlliamo sempre alla fine del ciclo
                self.auto_withdraw(target_address)

            return redeemed
            
        except Exception as e:
            log.error(f"❌ CRASH auto_redeem: {str(e)}")
            log.error(traceback.format_exc())
            return 0

    def auto_withdraw(self, safe_address):
        """Trasferisce USDC dal Safe al Wallet Metamask se il saldo > 1 USDC."""
        try:
            if safe_address.lower() == self.my_address.lower():
                return

            usdc_contract_addr = Web3.to_checksum_address(config.POLY_USDC)
            usdc_abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
                        {"inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}]
            usdc_contract = self.w3.eth.contract(address=usdc_contract_addr, abi=usdc_abi)
            
            bal = usdc_contract.functions.balanceOf(Web3.to_checksum_address(safe_address)).call()
            # Soglia: 1 USDC (USDC.e ha 6 decimali)
            if bal > 1000000:
                log.info(f"   ↳ 🏧 Saldo Safe: {bal/1e6} USDC. Avvio prelievo verso Metamask...")
                
                # Generazione firma Proxy Safe
                transfer_data = usdc_contract.functions.transfer(Web3.to_checksum_address(self.my_address), bal).build_transaction({
                    'from': self.my_address, 'nonce': 0, 'gas': 1, 'gasPrice': 1
                })['data']
                
                # ABI per execTransaction (Safe)
                SAFE_ABI = [{"inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "data", "type": "bytes"}, {"name": "operation", "type": "uint8"}, {"name": "safeTxGas", "type": "uint256"}, {"name": "baseGas", "type": "uint256"}, {"name": "gasPrice", "type": "uint256"}, {"name": "gasToken", "type": "address"}, {"name": "refundReceiver", "type": "address"}, {"name": "signatures", "type": "bytes"}], "name": "execTransaction", "outputs": [{"name": "success", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}]
                safe_contract = self.w3.eth.contract(address=Web3.to_checksum_address(safe_address), abi=SAFE_ABI)
                
                signature = "0x" + "000000000000000000000000" + self.my_address[2:].lower() + \
                            "0000000000000000000000000000000000000000000000000000000000000000" + "01"
                
                tx = safe_contract.functions.execTransaction(
                    usdc_contract_addr, 0, transfer_data, 0, 0, 0, 0,
                    "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000",
                    Web3.to_bytes(hexstr=signature)
                ).build_transaction({
                    'from': self.my_address,
                    'nonce': self.w3.eth.get_transaction_count(self.my_address),
                    'gas': 200000,
                    'gasPrice': int(self.w3.eth.gas_price * 1.3)
                })
                
                signed_tx = self.w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                log.info(f"   ↳ 🏧 ✅ Prelievo inviato! TX: {tx_hash.hex()[:15]}...")
                
        except Exception as e:
            log.warning(f"   ↳ 🏧 ❌ Errore durante il prelievo automatico: {e}")

    def get_positions(self):
        """Recupera solo le posizioni ATTIVE del 2026, ignorando lo storico obsoleto."""
        try:
            url = f"https://data-api.polymarket.com/positions?user={self.my_address}"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return []

            data = resp.json()
            # 1. Filtriamo posizioni con size minima e raccogliamo conditionId
            active_positions = [p for p in data if float(p.get('size', 0)) > 0.01]
            if not active_positions:
                return []

            condition_ids = list(set(p.get('conditionId') or p.get('condition_id') for p in active_positions))
            condition_ids = [cid for cid in condition_ids if cid]

            if not condition_ids:
                return []

            # 2. Recupero dati mercato in batch (max 20 per volta per URL length)
            market_lookup = {}
            for i in range(0, len(condition_ids), 20):
                batch = condition_ids[i:i+20]
                try:
                    g_url = f"https://gamma-api.polymarket.com/markets"
                    g_resp = requests.get(g_url, params={"conditionId": batch}, timeout=5)
                    if g_resp.status_code == 200:
                        for m in g_resp.json():
                            cid = m.get('conditionId')
                            if cid: market_lookup[cid] = m
                except Exception as e:
                    log.debug(f"Errore batch gamma-api: {e}")

            # 3. Processiamo le posizioni usando il lookup
            active = []
            for p in active_positions:
                cond_id = p.get('conditionId') or p.get('condition_id')
                market = market_lookup.get(cond_id)
                if not market:
                    continue

                # SALTA se il mercato è chiuso o troppo vecchio
                if "2020" in market.get('question', ''):
                    continue

                title = market.get('question', 'Match')

                # Filtro Strategia: Mostriamo solo crypto target e scommesse di prezzo
                q_low = title.lower()
                if not any(x in q_low for x in ["btc", "bitcoin", "eth", "ethereum", "price of", "up or down"]):
                    continue

                size = float(p.get('size', 0))
                entry = float(p.get('avg_price', 0))
                current = float(p.get('cur_price', 0)) or entry
                pnl = (current - entry) * size

                if size * current < 0.01: # Nascondi rimasugli a valore zero
                    continue

                active.append({
                    "title": title,
                    "size": size,
                    "side": "YES" if "yes" in p.get('slug', '').lower() else "NO",
                    "pnl": pnl,
                    "value": size * current
                })
            return active
            if resp.status_code == 200:
                data = resp.json()
                active = []
                for p in data:
                    size = float(p.get('size', 0))
                    # Filtriamo solo posizioni reali (anche frazionarie)
                    if size > 0.01:
                        cond_id = p.get('conditionId') or p.get('condition_id')
                        if not cond_id: continue
                        
                        # Recupero dati mercato per verificare se è attivo nel 2026
                        try:
                            g_url = f"https://gamma-api.polymarket.com/markets?conditionId={cond_id}"
                            g_resp = requests.get(g_url, timeout=5)
                            if g_resp.status_code == 200:
                                g_data = g_resp.json()
                                if g_data:
                                    market = g_data[0]
                                    # SALTA se il mercato è chiuso o troppo vecchio
                                    if "2020" in market.get('question', ''):
                                        continue
                                        
                                    title = market.get('question', 'Match')
                                    
                                    # Filtro Strategia: Mostriamo solo crypto target e scommesse di prezzo
                                    q_low = title.lower()
                                    if not any(x in q_low for x in ["btc", "bitcoin", "eth", "ethereum", "price of", "up or down"]):
                                        continue
                                        
                                    entry = float(p.get('avg_price', 0))
                                    current = float(p.get('cur_price', 0)) or entry
                                    pnl = (current - entry) * size
                                    
                                    if size * current < 0.01: # Nascondi rimasugli a valore zero
                                        continue

                                    active.append({
                                        "title": title,
                                        "size": size,
                                        "side": "YES" if "yes" in p.get('slug', '').lower() else "NO",
                                        "pnl": pnl,
                                        "value": size * current
                                    })
                        except Exception as inner_e:
                            log.debug(f"Errore processamento singola posizione: {inner_e}")
                return active
            return []
        except Exception as e:
            log.warning(f"Errore recupero posizioni: {e}")
            return []


    def check_take_profit(self, threshold=0.20):
        """Scansiona le posizioni attive e vende se il profitto per share supera la soglia."""
        try:
            url = f"https://data-api.polymarket.com/positions?user={self.my_address}"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return

            positions = resp.json()
            for p in positions:
                size = float(p.get('size', 0))
                if size <= 0.01:
                    continue

                entry_price = float(p.get('avg_price', 0))
                token_id = p.get('asset')
                
                if not token_id:
                    continue
                    
                # Ottieni il prezzo reale dal Book aggiornato!
                try:
                    ob = self.client.get_order_book(token_id)
                    current_price = float(ob.bids[0].price) if ob.bids else 0
                except Exception as e:
                    # In caso di errore API, fallback
                    log.debug(f"Impossibile leggere book per take profit {token_id}: {e}")
                    current_price = float(p.get('cur_price', 0)) or entry_price

                if current_price - entry_price >= threshold:
                    log.info(f"🎯 TAKE PROFIT TRIGGERED! Token {token_id[:10]}... | Entry: ${entry_price:.2f} | Current (Bid): ${current_price:.2f} | Size: {size}")
                    try:
                        # Format size to max 2 decimals to avoid CLOB precision errors
                        formatted_size = round(size, 2)
                        
                        from py_clob_client.clob_types import MarketOrderArgs
                        signed_order = self.client.create_market_order(MarketOrderArgs(
                            amount=formatted_size,
                            side="SELL",
                            token_id=token_id
                        ))
                        resp = self.client.post_order(signed_order)
                        
                        if resp.get('success') or resp.get('orderID') or resp.get('order_id'):
                            log.info(f"✅ Ordine SELL (TP) ESEGUITO per {token_id[:10]} | Resp: {resp}")
                        else:
                            log.error(f"❌ Ordine SELL (TP) RIFIUTATO dal CLOB: {resp}")
                    except Exception as e:
                        log.error(f"❌ Errore durante la vendita Take Profit: {e}")
        except Exception as e:
            log.warning(f"Errore in check_take_profit: {e}")

    def emergency_sell_all(self):

        """Vende le posizioni e CANCELLA tutti gli ordini aperti per sbloccare i fondi."""
        try:
            # 1. Cancella tutti gli ordini aperti (sblocca USDC.e impegnati)
            log.info("🚫 Cancellazione ordini aperti...")
            self.client.cancel_all_orders()
            
            # 2. Vende le posizioni attive
            url = f"https://data-api.polymarket.com/positions?user={self.my_address}"
            data = requests.get(url).json()
            for p in data:
                size = float(p.get('size', 0))
                token_id = p.get('asset')
                if size > 0.1 and token_id:
                    log.info(f"🚨 LIQUIDAZIONE: Vendo token {token_id}")
                    try:
                        from py_clob_client.clob_types import OrderArgs
                        signed_order = self.client.create_order(OrderArgs(
                            price=0.01, # Prezzo limite minimo per sweep quasi totale
                            size=round(size, 2),
                            side="SELL",
                            token_id=token_id
                        ))
                        self.client.post_order(signed_order)
                    except Exception as inner_e:
                        log.error(f"Errore durante la vendita di emergenza del token {token_id}: {inner_e}")
        except Exception as e:
            log.error(f"Errore durante liquidazione: {e}")

    def get_trade_history(self):
        """Recupera la cronologia reale degli scambi conclusi (Trades)."""
        try:
            # get_trades restituisce gli scambi effettivamente eseguiti on-chain
            resp = self.client.get_trades()
            history = []
            for t in resp:
                history.append({
                    "id": t.get('id', '')[-6:],
                    "asset": t.get('market', 'Match').split('/')[-1][:15], # Nome breve
                    "side": t.get('side'),
                    "size": float(t.get('size', 0)),
                    "price": float(t.get('price', 0)),
                    "time": t.get('timestamp')
                })
            return history[:10]
        except Exception as e:
            log.warning(f"Errore recupero trades: {e}")
            return []
