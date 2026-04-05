import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Configurazione
RPC_URL = "https://polygon-rpc.com"
WALLET_ADDRESS = "0x27Fb2C57b1149bE45d99070a906753D5A8ad6e3a"
PROXY_FRONT = "0x3A1c6640daeAc3513726F06A9f03911CC1080251"
PRIVATE_KEY = os.getenv("HOT_WALLET_PRIVATE_KEY")

# Token USDC su Polygon
USDC_NATIVE = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# ABI minima per ERC20 (balanceOf, allowance, approve)
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

def setup_wallet():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("Errore: Impossibile connettersi all'RPC di Polygon.")
        return

    print(f"Connesso a Polygon. Wallet: {WALLET_ADDRESS}")

    # 1. Check Saldo POL
    pol_balance = w3.eth.get_balance(WALLET_ADDRESS)
    print(f"Saldo POL: {w3.from_wei(pol_balance, 'ether'):.4f} POL")

    # 2. Check USDC
    tokens = {"USDC Native": USDC_NATIVE, "USDC (bridged)": USDC_BRIDGED}
    active_token = None
    
    for name, addr in tokens.items():
        contract = w3.eth.contract(address=w3.to_checksum_address(addr), abi=ERC20_ABI)
        try:
            balance = contract.functions.balanceOf(WALLET_ADDRESS).call()
            decimals = contract.functions.decimals().call()
            readable_balance = balance / (10**decimals)
            print(f"Saldo {name}: {readable_balance:.2f}")
            
            if readable_balance > 0:
                active_token = (name, addr, contract, decimals)
        except Exception as e:
            print(f"Errore nel check {name}: {e}")

    if not active_token:
        print("Nessun saldo USDC trovato su Native o Bridged. Carica dei fondi!")
        return

    name, addr, contract, decimals = active_token
    print(f"\nUtilizzo {name} ({addr}) per le operazioni.")

    # 3. Check Allowance
    allowance = contract.functions.allowance(WALLET_ADDRESS, PROXY_FRONT).call()
    needed = 10 * (10**decimals)
    
    if allowance < needed:
        print(f"Allowance insufficiente ({allowance}). Invio Approve...")
        if not PRIVATE_KEY:
            print("ERRORE: HOT_WALLET_PRIVATE_KEY non trovata nel .env")
            return

        # Costruisce la transazione di approve
        amount_to_approve = 2**256 - 1 # Infinite approval per comodità
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        
        tx = contract.functions.approve(PROXY_FRONT, amount_to_approve).build_transaction({
            'from': WALLET_ADDRESS,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Transazione di Approve inviata! Hash: {w3.to_hex(tx_hash)}")
        print("Attendi la conferma sulla blockchain.")
    else:
        print(f"Allowance OK: {allowance / (10**decimals):.2f} USDC autorizzati per Azuro.")

if __name__ == "__main__":
    setup_wallet()
