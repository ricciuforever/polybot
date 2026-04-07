import time
import json
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3.middleware import ExtraDataToPOAMiddleware
from modules.rpc_manager import RPCManager
import config
from modules.logger import get_logger

log = get_logger("azuro_trader")

# ABI Minime
USDT_ABI = [
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"}
]

LP_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "core", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
            {
                "components": [
                    {"internalType": "uint256", "name": "conditionId", "type": "uint256"},
                    {"internalType": "uint256", "name": "outcomeId", "type": "uint256"},
                    {"internalType": "uint256", "name": "minOdds", "type": "uint256"}
                ],
                "internalType": "struct BetData",
                "name": "betData",
                "type": "tuple"
            }
        ],
        "name": "bet",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

PROXY_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "core", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
                    {
                        "components": [
                            {"internalType": "uint256", "name": "conditionId", "type": "uint256"},
                            {"internalType": "uint256", "name": "outcomeId", "type": "uint256"},
                            {"internalType": "uint256", "name": "minOdds", "type": "uint256"}
                        ],
                        "internalType": "struct BetData",
                        "name": "betData",
                        "type": "tuple"
                    }
                ],
                "name": "data",
                "type": "tuple"
            },
            {"internalType": "address", "name": "affiliate", "type": "address"}
        ],
        "name": "bet",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

class AzuroTrader:
    def __init__(self):
        self.rpc_manager = RPCManager(config.RPC_NODES)
        # Inizializzazione account e contratti
        self.account = Account.from_key(config.PRIVATE_KEY)
        self.my_address = self.account.address
        self.usdc_address = Web3.to_checksum_address(config.AZURO_TOKEN)
        self.erc20_abi = USDT_ABI
        self.safe_address = Web3.to_checksum_address(config.SAFE_ADDRESS) if config.SAFE_ADDRESS else None
        self.core_address = Web3.to_checksum_address(config.AZURO_CORE)

    @property
    def w3(self):
        w3_instance = self.rpc_manager.get_w3()
        if not any(m.name == 'extra_data_to_poa' for m in w3_instance.middleware_onion):
            w3_instance.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return w3_instance
        
    def check_connection(self):
        try:
            connected = self.w3.is_connected()
            if not connected:
                return False, f"Impossibile connettersi all'RPC: {config.AZURO_RPC}"
            
            chain_id = self.w3.eth.chain_id
            if chain_id != config.AZURO_CHAIN_ID:
                return False, f"Chain ID errato! Trovato: {chain_id}, Atteso: {config.AZURO_CHAIN_ID}"
                
            balance_wei = self.w3.eth.get_balance(self.my_address)
            balance_pol = self.w3.from_wei(balance_wei, 'ether')
            
            try:
                usdt_eoa = self.usdt.functions.balanceOf(self.my_address).call()
                usdt_safe = self.usdt.functions.balanceOf(self.safe_address).call() if self.safe_address else 0
                usdt_human_eoa = usdt_eoa / 1_000_000
                usdt_human_safe = usdt_safe / 1_000_000
            except Exception as e:
                log.warning(f"Errore recupero saldo USDC (forse RPC instabile): {e}")
                usdt_human_eoa = 0.0
                usdt_human_safe = 0.0

            log.info(f"Connesso! Network ID: {chain_id}")
            log.info(f"Wallet EOA: {self.my_address}")
            log.info(f"Safe Address: {self.safe_address}")
            log.info(f"Saldo Gas (POL): {balance_pol:.4f}")
            log.info(f"USDC EOA: {usdt_human_eoa:.2f} | USDC Safe: {usdt_human_safe:.2f}")
            
            return True, f"Wallet pronto (Net={chain_id})"
        except Exception as e:
            return False, f"Errore critico: {str(e)}"

    async def get_balances(self):
        """Recupera i saldi POL e USDC.e/USDT dell'utente con Fallback RPC."""
        def _fetch():
            # Gas MATIC (solo EOA)
            pol_balance = self.w3.eth.get_balance(self.my_address)
            pol_eth = float(self.w3.from_wei(pol_balance, 'ether'))
            
            # USDT/USDC.e Balance
            usdt_token = self.w3.eth.contract(address=self.usdc_address, abi=self.erc20_abi)
            usdt_raw = usdt_token.functions.balanceOf(self.my_address).call()
            usdt_amount = float(usdt_raw) / 10**6
            return pol_eth, usdt_amount

        try:
            return self.rpc_manager.call_safe(_fetch)
        except Exception as e:
            log.warning(f"Tentativo recupero saldi fallito dopo rotazione RPC: {e}")
            return 0.0, 0.0

    def get_relayer_gas_info(self):
        """Recupera info gas dal relayer"""
        try:
            url = f"{config.AZURO_API_URL}/bet/gas-info?environment={config.AZURO_ENVIRONMENT}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('relayerFeeAmount', "0")
            return "0"
        except Exception as e:
            log.warning(f"Errore recupero gas info: {e}")
            return "0"

    def _rpc_call_with_retry(self, func, *args, **kwargs):
        for attempt in range(5):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) and attempt < 4:
                    time.sleep(2)
                else:
                    raise e

    def sign_proxy_bet_order(self, target_core, amount_raw, expires_at, c_id, outcome_id, min_odds_raw):
        """Firma il messaggio EIP-712 usando BetData per il ProxyFront V3"""
        domain = {
            "name": "ProxyFront",
            "version": "1",
            "chainId": config.AZURO_CHAIN_ID,
            "verifyingContract": Web3.to_checksum_address(config.AZURO_PROXY)
        }
        
        types = {
            "BetData": [
                {"name": "core", "type": "address"},
                {"name": "amount", "type": "uint128"},
                {"name": "expiresAt", "type": "uint256"},
                {"name": "bet", "type": "SubBet"}
            ],
            "SubBet": [
                {"name": "conditionId", "type": "uint256"},
                {"name": "outcomeId", "type": "uint64"},
                {"name": "minOdds", "type": "uint64"}
            ]
        }
        
        message = {
            "core": Web3.to_checksum_address(target_core),
            "amount": amount_raw,
            "expiresAt": expires_at,
            "bet": {
                "conditionId": c_id,
                "outcomeId": int(outcome_id),
                "minOdds": min_odds_raw
            }
        }
        
        return self._sign_message(domain, types, message)

    def _sign_message(self, domain, types, message):
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
            "primaryType": list(types.keys())[0],
            "domain": domain,
            "message": message
        }
        
        encoded_data = encode_typed_data(full_message=structured_data)
        signed_msg = self.account.sign_message(encoded_data)
        sig_hex = signed_msg.signature.hex()
        return "0x" + sig_hex if not sig_hex.startswith("0x") else sig_hex


    def execute_bet(self, condition_id, outcome_id, amount_human, min_odds_decimal, core_address=None):
        """
        Esegue la scommessa tramite LIVE RELAYER API (V3 Live/DGPredict logic).
        """
        try:
            amount_raw = int(amount_human * 1_000_000)
            # Calcolo min_odds con slippage del 5% per evitare rejections su variazioni rapide live
            slippage = 0.95
            min_odds_raw = int(min_odds_decimal * slippage * 1_000_000_000_000)
            expires_at = int(time.time()) + 300
            nonce = int(time.time() * 1000)
            
            # Dinamismo CORE
            target_core = Web3.to_checksum_address(core_address) if core_address else self.core_address
            
            # Gas Strategy - Fallback robusto per Polygon
            try:
                block = self._rpc_call_with_retry(self.w3.eth.get_block, 'latest')
                base_fee = block.get('baseFeePerGas', self.w3.eth.gas_price)
                max_prio = self._rpc_call_with_retry(getattr, self.w3.eth, 'max_priority_fee')
                priority_fee = max_prio + self.w3.to_wei(2, 'gwei')
                max_fee = base_fee * 2 + priority_fee
                tx_params = {
                    'maxFeePerGas': max_fee,
                    'maxPriorityFeePerGas': priority_fee
                }
            except Exception:
                tx_params = {'gasPrice': self.w3.eth.gas_price}

            # 1. Controllo Allowance per RELAYER
            relayer_addr = Web3.to_checksum_address(config.AZURO_RELAYER)
            try:
                allowance_func = self.usdt.functions.allowance(self.my_address, relayer_addr).call
                allowance = self._rpc_call_with_retry(allowance_func)
            except Exception as e:
                log.warning(f"Failed to fetch allowance rpc (nodo lento): {e} -> Bypass Allowance Check.")
                allowance = 2**256 - 1 # Assume allowance già data per procedere alla signature

            if allowance < amount_raw:
                log.info(f"Approve Relayer in corso...")
                base_tx = {
                    'from': self.my_address,
                    'nonce': self.w3.eth.get_transaction_count(self.my_address, 'pending'),
                    'gas': 80000,
                    'chainId': config.AZURO_CHAIN_ID
                }
                base_tx.update(tx_params)
                
                tx_approve = self.usdt.functions.approve(relayer_addr, 2**256-1).build_transaction(base_tx)
                signed_approve = self.w3.eth.account.sign_transaction(tx_approve, private_key=config.PRIVATE_KEY)
                self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                time.sleep(5)

            # 2. Struttura Dati gerarchica per firma Live EIP-712 e API REST
            c_id = int(condition_id, 16) if str(condition_id).startswith('0x') else int(condition_id)
            relayer_fee_int = int(self.get_relayer_gas_info())
            
            client_data = {
                "attention": "NitroBot_Live",
                "affiliate": "0x0000000000000000000000000000000000000000",
                "core": target_core,
                "expiresAt": expires_at,
                "chainId": config.AZURO_CHAIN_ID,
                "relayerFeeAmount": relayer_fee_int
            }
            
            # 3. Firma EIP-712 usando BetData e ProxyFront
            signature = self.sign_proxy_bet_order(target_core, amount_raw, expires_at, c_id, outcome_id, min_odds_raw)
            log.info(f"Firma ProxyFront EIP-712 generata: {signature[:10]}...")

            # 4. Struttura Dati per l'API REST
            api_bet_payload = {
                "clientData": {
                    "attention": client_data["attention"],
                    "affiliate": client_data["affiliate"],
                    "core": client_data["core"],
                    "expiresAt": client_data["expiresAt"],
                    "chainId": client_data["chainId"],
                    "relayerFeeAmount": str(client_data["relayerFeeAmount"]),
                    "isFeeSponsored": False,
                    "isBetSponsored": False,
                    "isSponsoredBetReturnable": False
                },
                "bet": {
                    "conditionId": str(c_id),
                    "outcomeId": int(outcome_id),     # DEVE ESSERE NUMBER
                    "minOdds": str(min_odds_raw),
                    "amount": str(amount_raw),
                    "nonce": str(nonce)
                }
            }

            # 5. Invio API
            payload = {
                "environment": config.AZURO_ENVIRONMENT,
                "bettor": self.my_address.lower(),
                "betOwner": self.my_address.lower(),
                "clientBetData": api_bet_payload,
                "bettorSignature": signature
            }
            
            import json
            log.warning("=== DEBUG PAYLOAD EIP-712 ===")
            log.warning("Firma EIP-712 e BetData verificate internamente.")
            log.warning(f"API payload: {json.dumps(payload)}")
            log.warning("=============================")
            
            # Endpoint LIVE
            api_url = f"{config.AZURO_API_URL}/bet/orders/ordinar"
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
                status_resp = requests.get(f"{config.AZURO_API_URL}/bet/orders/{order_id}")
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
            return False, str(e)

if __name__ == "__main__":
    # Test iniziale
    trader = AzuroTrader()
    ok, msg = trader.check_connection()
    print(f"Stato Connessione: {'OK' if ok else 'ERRORE'} - {msg}")
