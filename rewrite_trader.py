import re

with open('azuro_trader.py', 'r') as f:
    content = f.read()

# I need to completely replace sign_bet_order and execute_bet functions to support Live Betting logic.

old_sign_func = """    def sign_bet_order(self, client_bet_data):
        \"\"\"Firma il messaggio EIP-712 per il relayer\"\"\"
        domain = {
            "name": "Relayer",
            "version": "1",
            "chainId": config.AZURO_CHAIN_ID,
            "verifyingContract": Web3.to_checksum_address(config.AZURO_RELAYER)
        }
        
        types = {
            "ClientBetData": [
                {"name": "clientData", "type": "ClientData"},
                {"name": "bet", "type": "SubBet"}
            ],
            "ClientData": [
                {"name": "attention", "type": "string"},
                {"name": "affiliate", "type": "address"},
                {"name": "core", "type": "address"},
                {"name": "expiresAt", "type": "uint256"},
                {"name": "chainId", "type": "uint256"},
                {"name": "relayerFeeAmount", "type": "uint256"},
                {"name": "isBetSponsored", "type": "bool"},
                {"name": "isFeeSponsored", "type": "bool"},
                {"name": "isSponsoredBetReturnable", "type": "bool"}
            ],
            "SubBet": [
                {"name": "conditionId", "type": "uint256"},
                {"name": "outcomeId", "type": "uint128"},
                {"name": "minOdds", "type": "uint64"},
                {"name": "amount", "type": "uint128"},
                {"name": "nonce", "type": "uint256"}
            ]
        }
        
        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                **types
            },
            "primaryType": "ClientBetData",
            "domain": domain,
            "message": client_bet_data
        }
        
        encoded_data = encode_typed_data(full_message=structured_data)
        signed_msg = self.account.sign_message(encoded_data)
        sig_hex = signed_msg.signature.hex()
        return "0x" + sig_hex if not sig_hex.startswith("0x") else sig_hex"""

new_sign_func = """    def sign_live_bet_order(self, live_order, core_address):
        \"\"\"Firma il messaggio EIP-712 per le Live Bets (DGPredict)\"\"\"
        domain = {
            "name": "Live Betting",
            "version": "1.0.0",
            "chainId": config.AZURO_CHAIN_ID,
            "verifyingContract": Web3.to_checksum_address(core_address)
        }
        
        types = {
            "ClientBetData": [
                {"name": "attention", "type": "string"},
                {"name": "affiliate", "type": "address"},
                {"name": "core", "type": "address"},
                {"name": "amount", "type": "uint128"},
                {"name": "nonce", "type": "uint256"},
                {"name": "conditionId", "type": "uint256"},
                {"name": "outcomeId", "type": "uint64"},
                {"name": "minOdds", "type": "uint64"},
                {"name": "expiresAt", "type": "uint256"},
                {"name": "chainId", "type": "uint256"},
                {"name": "relayerFeeAmount", "type": "uint256"}
            ]
        }
        
        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                **types
            },
            "primaryType": "ClientBetData",
            "domain": domain,
            "message": live_order
        }
        
        encoded_data = encode_typed_data(full_message=structured_data)
        signed_msg = self.account.sign_message(encoded_data)
        sig_hex = signed_msg.signature.hex()
        return "0x" + sig_hex if not sig_hex.startswith("0x") else sig_hex"""

old_exec_func = """    def execute_bet(self, condition_id, outcome_id, amount_human, min_odds_decimal, core_address=None):
        \"\"\"
        Esegue la scommessa tramite RELAYER API (V3 Live/DGPredict logic).
        \"\"\"
        try:
            amount_raw = int(amount_human * 1_000_000)
            min_odds_raw = int(min_odds_decimal * 1_000_000_000_000)
            expires_at = int(time.time()) + 300
            nonce = int(time.time() * 1000)
            
            # Dinamismo CORE
            target_core = Web3.to_checksum_address(core_address) if core_address else self.core_address
            
            # Gas Strategy (EIP-1559)
            base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
            priority_fee = self.w3.eth.max_priority_fee + self.w3.to_wei(2, 'gwei')
            max_fee = base_fee * 2 + priority_fee

            # 1. Controllo Allowance per RELAYER
            relayer_addr = Web3.to_checksum_address(config.AZURO_RELAYER)
            allowance = self.usdt.functions.allowance(self.my_address, relayer_addr).call()

            if allowance < amount_raw:
                log.info(f"Approve Relayer in corso...")
                tx_approve = self.usdt.functions.approve(relayer_addr, 2**256-1).build_transaction({
                    'from': self.my_address,
                    'nonce': self.w3.eth.get_transaction_count(self.my_address, 'pending'),
                    'gas': 80000,
                    'chainId': config.AZURO_CHAIN_ID
                })
                signed_approve = self.w3.eth.account.sign_transaction(tx_approve, private_key=config.PRIVATE_KEY)
                self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                time.sleep(5)

            # 2. Struttura Dati per la firma EIP-712 (usa interi per web3.py)
            c_id = int(condition_id, 16) if str(condition_id).startswith('0x') else int(condition_id)
            relayer_fee_int = int(self.get_relayer_gas_info())
            
            client_bet_data_sign = {
                "clientData": {
                    "attention": "Azuro Sniper Bot",
                    "affiliate": "0x0000000000000000000000000000000000000000",
                    "core": target_core,
                    "expiresAt": expires_at,
                    "chainId": config.AZURO_CHAIN_ID,
                    "relayerFeeAmount": relayer_fee_int,
                    "isBetSponsored": False,
                    "isFeeSponsored": False,
                    "isSponsoredBetReturnable": False
                },
                "bet": {
                    "conditionId": c_id,
                    "outcomeId": int(outcome_id),
                    "minOdds": min_odds_raw,
                    "amount": amount_raw,
                    "nonce": nonce
                }
            }
            
            # 3. Firma EIP-712
            signature = self.sign_bet_order(client_bet_data_sign)
            log.info(f"Firma EIP-712 generata: {signature[:10]}...")

            # 4. Struttura Dati per l'API REST (converte i grandi numeri in stringhe)
            api_client_bet_data = {
                "clientData": {
                    "attention": client_bet_data_sign["clientData"]["attention"],
                    "affiliate": client_bet_data_sign["clientData"]["affiliate"],
                    "core": client_bet_data_sign["clientData"]["core"],
                    "expiresAt": client_bet_data_sign["clientData"]["expiresAt"],
                    "chainId": client_bet_data_sign["clientData"]["chainId"],
                    "relayerFeeAmount": str(relayer_fee_int),
                    "isBetSponsored": client_bet_data_sign["clientData"]["isBetSponsored"],
                    "isFeeSponsored": client_bet_data_sign["clientData"]["isFeeSponsored"],
                    "isSponsoredBetReturnable": client_bet_data_sign["clientData"]["isSponsoredBetReturnable"]
                },
                "bet": {
                    "conditionId": str(c_id),
                    "outcomeId": int(outcome_id),
                    "minOdds": str(min_odds_raw),
                    "amount": str(amount_raw),
                    "nonce": str(nonce)
                }
            }

            # 5. Invio API
            payload = {
                "environment": config.AZURO_ENVIRONMENT, # Ora sarà "PolygonUSDT"
                "bettor": self.my_address,
                "betOwner": self.my_address,
                "clientBetData": api_client_bet_data,
                "bettorSignature": signature
            }
            
            api_url = f"{config.AZURO_API_URL}/bet/orders/ordinar"
            log.info(f"Invio ordine Relayer... | Core: {target_core}")
            
            resp = requests.post(api_url, json=payload, timeout=15)
            if resp.status_code not in [200, 201]:
                return False, f"API Error {resp.status_code}: {resp.text}"
            
            order_data = resp.json()
            order_id = order_data.get('id')
            log.info(f"🚀 Ordine inviato! ID: {order_id}")
            
            # Polling Stato Ordine
            for _ in range(12): # 36 secondi max
                time.sleep(3)
                status_resp = requests.get(f"{config.AZURO_API_URL}/bet/orders/{order_id}")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    state = status_data.get('state')
                    log.info(f"Stato ordine: {state}")
                    if state == 'Accepted':
                        tx_hash = status_data.get('txHash', 'N/A')
                        return True, tx_hash
                    elif state in ['Rejected', 'Canceled', 'Error']:
                        return False, f"Ordine fallito: {state}"
            return False, "Timeout attesa conferma ordine"

        except Exception as e:
            log.error(f"Errore durante l'esecuzione della bet: {e}")
            return False, str(e)"""

new_exec_func = """    def execute_bet(self, condition_id, outcome_id, amount_human, min_odds_decimal, core_address=None):
        \"\"\"
        Esegue la scommessa tramite LIVE RELAYER API (V3 Live/DGPredict logic).
        \"\"\"
        try:
            amount_raw = int(amount_human * 1_000_000)
            min_odds_raw = int(min_odds_decimal * 1_000_000_000_000)
            expires_at = int(time.time()) + 300
            nonce = int(time.time() * 1000)
            
            # Dinamismo CORE
            target_core = Web3.to_checksum_address(core_address) if core_address else self.core_address
            
            # Gas Strategy (EIP-1559)
            base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
            priority_fee = self.w3.eth.max_priority_fee + self.w3.to_wei(2, 'gwei')
            max_fee = base_fee * 2 + priority_fee

            # 1. Controllo Allowance per RELAYER
            relayer_addr = Web3.to_checksum_address(config.AZURO_RELAYER)
            allowance = self.usdt.functions.allowance(self.my_address, relayer_addr).call()

            if allowance < amount_raw:
                log.info(f"Approve Relayer in corso...")
                tx_approve = self.usdt.functions.approve(relayer_addr, 2**256-1).build_transaction({
                    'from': self.my_address,
                    'nonce': self.w3.eth.get_transaction_count(self.my_address, 'pending'),
                    'gas': 80000,
                    'chainId': config.AZURO_CHAIN_ID
                })
                signed_approve = self.w3.eth.account.sign_transaction(tx_approve, private_key=config.PRIVATE_KEY)
                self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                time.sleep(5)

            # 2. Struttura Dati per la firma EIP-712 (Live Bets)
            c_id = int(condition_id, 16) if str(condition_id).startswith('0x') else int(condition_id)
            relayer_fee_int = int(self.get_relayer_gas_info())
            
            live_order_sign = {
                "attention": "Azuro Sniper Bot",
                "affiliate": "0x0000000000000000000000000000000000000000",
                "core": target_core,
                "amount": amount_raw,
                "nonce": nonce,
                "conditionId": c_id,
                "outcomeId": int(outcome_id),
                "minOdds": min_odds_raw,
                "expiresAt": expires_at,
                "chainId": config.AZURO_CHAIN_ID,
                "relayerFeeAmount": relayer_fee_int
            }
            
            # 3. Firma EIP-712
            signature = self.sign_live_bet_order(live_order_sign, target_core)
            log.info(f"Firma EIP-712 generata: {signature[:10]}...")

            # 4. Struttura Dati per l'API REST (converte i numeri in stringhe)
            api_bet_payload = {
                "attention": live_order_sign["attention"],
                "affiliate": live_order_sign["affiliate"],
                "core": live_order_sign["core"],
                "amount": str(live_order_sign["amount"]),
                "nonce": str(live_order_sign["nonce"]),
                "conditionId": str(live_order_sign["conditionId"]),
                "outcomeId": live_order_sign["outcomeId"], # L'outcomeId nell'API live spesso resta Number, oppure lo castiamo. In SDK usavano +outcomeId
                "minOdds": str(live_order_sign["minOdds"]),
                "expiresAt": live_order_sign["expiresAt"],
                "chainId": live_order_sign["chainId"],
                "relayerFeeAmount": str(live_order_sign["relayerFeeAmount"])
            }

            # 5. Invio API
            payload = {
                "environment": config.AZURO_ENVIRONMENT,
                "bettor": self.my_address.lower(),
                "data": {
                    "bet": api_bet_payload
                },
                "bettorSignature": signature
            }
            
            # Endpoint LIVE
            api_url = f"{config.AZURO_API_URL}/orders"
            log.info(f"Invio ordine LIVE Relayer... | Core: {target_core}")
            
            resp = requests.post(api_url, json=payload, timeout=15)
            if resp.status_code not in [200, 201]:
                return False, f"API Error {resp.status_code}: {resp.text}"
            
            order_data = resp.json()
            order_id = order_data.get('id')
            log.info(f"🚀 Ordine LIVE inviato! ID: {order_id}")
            
            # Polling Stato Ordine
            for _ in range(12): # 36 secondi max
                time.sleep(3)
                status_resp = requests.get(f"{config.AZURO_API_URL}/orders/{order_id}")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    state = status_data.get('state')
                    log.info(f"Stato ordine: {state}")
                    if state == 'Accepted':
                        tx_hash = status_data.get('txHash', 'N/A')
                        return True, tx_hash
                    elif state in ['Rejected', 'Canceled', 'Error']:
                        return False, f"Ordine fallito: {state} - {status_data.get('errorMessage')}"
            return False, "Timeout attesa conferma ordine"

        except Exception as e:
            log.error(f"Errore durante l'esecuzione della bet LIVE: {e}")
            return False, str(e)"""

content = content.replace(old_sign_func, new_sign_func)
content = content.replace(old_exec_func, new_exec_func)

with open('azuro_trader.py', 'w') as f:
    f.write(content)
print("Rewrote azuro_trader.py successfully.")
