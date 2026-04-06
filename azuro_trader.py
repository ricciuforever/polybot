import time
import json
from web3 import Web3
from eth_account import Account
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

class AzuroTrader:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config.AZURO_RPC))
        self.account = Account.from_key(config.PRIVATE_KEY)
        self.my_address = self.account.address
        
        self.usdt = self.w3.eth.contract(address=Web3.to_checksum_address(config.AZURO_TOKEN), abi=USDT_ABI)
        self.lp = self.w3.eth.contract(address=Web3.to_checksum_address(config.AZURO_LP), abi=LP_ABI)
        
        self.core_address = Web3.to_checksum_address(config.AZURO_CORE)
        
    def check_connection(self):
        try:
            connected = self.w3.is_connected()
            if not connected:
                return False, f"Impossibile connettersi all'RPC: {config.AZURO_RPC}"
            
            chain_id = self.w3.eth.chain_id
            if chain_id != 137:
                return False, f"Chain ID errato! Trovato: {chain_id}, Atteso: 137 (Polygon)"
                
            balance_wei = self.w3.eth.get_balance(self.my_address)
            balance_pol = self.w3.from_wei(balance_wei, 'ether')
            
            try:
                usdt_bal = self.usdt.functions.balanceOf(self.my_address).call()
                usdt_human = usdt_bal / 1_000_000
            except Exception as e:
                log.warning(f"Errore recupero saldo USDT (forse RPC instabile): {e}")
                usdt_human = 0.0

            log.info(f"Connesso! Network ID: {chain_id}")
            log.info(f"Wallet: {self.my_address}")
            log.info(f"Saldo Gas (POL): {balance_pol:.4f}")
            log.info(f"Saldo USDT: {usdt_human:.2f}")
            
            return True, f"Wallet pronto (Net={chain_id})"
        except Exception as e:
            return False, f"Errore critico: {str(e)}"

    def get_balances(self):
        """Ritorna (pol_balance, usdc_balance)"""
        try:
            pol_wei = self.w3.eth.get_balance(self.my_address)
            pol_bal = float(self.w3.from_wei(pol_wei, 'ether'))
            
            usdc_bal_raw = self.usdt.functions.balanceOf(self.my_address).call()
            usdc_bal = float(usdc_bal_raw / 1_000_000)
            
            return pol_bal, usdc_bal
        except Exception as e:
            log.error(f"Errore recupero saldi: {e}")
            return 0.0, 0.0

    def execute_bet(self, condition_id, outcome_id, amount_human, min_odds_decimal):
        """
        Esegue lp.bet() su Azuro V3.
        amount_human: USD (es. 2.0)
        min_odds_decimal: Quote minime (es. 1.80)
        """
        try:
            amount_raw = int(amount_human * 1_000_000)
            # Azuro Odds sono in scala 10^12
            min_odds_raw = int(min_odds_decimal * 1_000_000_000_000)
            
            # Scadenza transazione (ora + 5 min)
            expires_at = int(time.time()) + 300
            
            # 1. Controllo Allowance
            allowance = self.usdt.functions.allowance(self.my_address, self.lp.address).call()
            if allowance < amount_raw:
                log.info(f"Allowance insufficient ({allowance} < {amount_raw}). Esecuzione Approve...")
                max_int = 2**256 - 1
                tx_approve = self.usdt.functions.approve(self.lp.address, max_int).build_transaction({
                    'from': self.my_address,
                    'nonce': self.w3.eth.get_transaction_count(self.my_address),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price
                })
                signed_approve = self.w3.eth.account.sign_transaction(tx_approve, private_key=config.PRIVATE_KEY)
                tx_hash_approve = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                log.info(f"✅ Approve inviata! Hash: {self.w3.to_hex(tx_hash_approve)}")
                time.sleep(2) # Breve attesa per propagazione
            
            # 2. Bet Data
            bet_data = (
                int(condition_id),
                int(outcome_id),
                min_odds_raw
            )
            
            log.info(f"Piazzamento Bet: Cond {condition_id} | Out {outcome_id} | Amt {amount_human} USDT")
            
            # 3. Costruzione Transazione
            tx = self.lp.functions.bet(
                self.core_address,
                amount_raw,
                expires_at,
                bet_data
            ).build_transaction({
                'from': self.my_address,
                'nonce': self.w3.eth.get_transaction_count(self.my_address),
                'gas': 400000, # Stima generosa per Azuro
                'gasPrice': self.w3.eth.gas_price
                # Nota: su Polygon V2 (EIP-1559) sarebbe meglio usare maxFeePerGas
            })
            
            # Firma e invio
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=config.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            log.info(f"✅ Bet inviata! Hash: {self.w3.to_hex(tx_hash)}")
            return True, self.w3.to_hex(tx_hash)

        except Exception as e:
            log.error(f"Errore durante l'esecuzione della bet: {e}")
            return False, str(e)

if __name__ == "__main__":
    # Test iniziale
    trader = AzuroTrader()
    ok, msg = trader.check_connection()
    print(f"Stato Connessione: {'OK' if ok else 'ERRORE'} - {msg}")
