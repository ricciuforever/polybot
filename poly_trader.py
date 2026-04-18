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

log = logging.getLogger("poly_trader")

class PolyTrader:
    """Gestisce il trading on-chain su Polymarket tramite CLOB API."""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config.AZURO_RPC))
        self.account = Account.from_key(config.PRIVATE_KEY)
        self.my_address = self.account.address
        
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

        # ABI ERC20
        self.usdc_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}, {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"}]
        self.usdc_contract = self.w3.eth.contract(address=Web3.to_checksum_address(config.POLY_USDC), abi=self.usdc_abi)

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
        except: pass

    def get_balances(self):
        try:
            pol = self.w3.eth.get_balance(self.my_address)
            usdc = self.usdc_contract.functions.balanceOf(self.my_address).call()
            return float(self.w3.from_wei(pol, 'ether')), float(usdc) / 1_000_000
        except: return 0.0, 0.0

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
                except: pass
            return False, error_msg

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

    def get_positions(self):
        """Recupera solo le posizioni ATTIVE del 2026, ignorando lo storico obsoleto."""
        try:
            url = f"https://data-api.polymarket.com/positions?user={self.my_address}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                active = []
                for p in data:
                    size = float(p.get('size', 0))
                    # Filtriamo solo posizioni reali (anche frazionarie)
                    if size > 0.01:
                        cond_id = p.get('condition_id')
                        
                        # Recupero dati mercato per verificare se è attivo nel 2026
                        try:
                            g_url = f"https://gamma-api.polymarket.com/markets?conditionId={cond_id}"
                            g_resp = requests.get(g_url, timeout=5)
                            if g_resp.status_code == 200:
                                g_data = g_resp.json()
                                if g_data:
                                    market = g_data[0]
                                    # SALTA se il mercato è chiuso o troppo vecchio
                                    if market.get('closed') or "2020" in market.get('question', ''):
                                        continue
                                        
                                    title = market.get('question', 'Match')
                                    
                                    # Filtro Strategia: Mostriamo solo BTC e scommesse di prezzo
                                    q_low = title.lower()
                                    if not any(x in q_low for x in ["btc", "bitcoin", "price of", "up or down"]):
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
                        except: pass
                return active
            return []
        except Exception as e:
            log.warning(f"Errore recupero posizioni: {e}")
            return []

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
                        self.client.create_order(OrderArgs(
                            price=0.05, # Prezzo molto basso per garantire fill immediato
                            size=size,
                            side="SELL",
                            token_id=token_id
                        ))
                    except: pass
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
