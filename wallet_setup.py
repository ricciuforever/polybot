import os
import json
from web3 import Web3
import config
from modules.logger import get_logger

log = get_logger("wallet_setup")

# ABI minima per ERC20 (balanceOf, allowance, approve)
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

def setup_wallet():
    # Bypass whitelist Alchemy origin
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
    }
    w3 = Web3(Web3.HTTPProvider(config.AZURO_RPC, request_kwargs={'headers': headers}))
    
    if not w3.is_connected():
        log.error("Errore: Impossibile connettersi all'RPC di Polygon (Alchemy Whitelist fail).")
        return

    wallet_addr = config.WALLET_ADDRESS
    lp_addr = config.AZURO_LP
    token_addr = config.AZURO_TOKEN

    log.info(f"Connesso a Polygon. Wallet: {wallet_addr}")
    log.info(f"Target Spender (Azuro V3 LP): {lp_addr}")

    # 1. Check Saldo POL
    pol_balance = w3.eth.get_balance(wallet_addr)
    log.info(f"Saldo POL: {w3.from_wei(pol_balance, 'ether'):.4f} POL")

    # 2. Check Token Balance
    contract = w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI)
    try:
        balance = contract.functions.balanceOf(wallet_addr).call()
        decimals = contract.functions.decimals().call()
        readable_balance = balance / (10**decimals)
        log.info(f"Saldo USDT: {readable_balance:.2f}")
        
        if readable_balance <= 0:
            log.warning("Saldo USDT insufficiente per scommettere.")
            return

        # 3. Check Allowance verso il nuovo LP V3
        allowance = contract.functions.allowance(wallet_addr, lp_addr).call()
        needed = 10 * (10**decimals) # Autorizziamo almeno 10 USDC
        
        if allowance < needed:
            log.info(f"Allowance insufficiente ({allowance}). Esecuzione Approve...")
            if not config.PRIVATE_KEY or config.PRIVATE_KEY == "0x...":
                log.error("ERRORE: PRIVATE_KEY non valida nel .env")
                return

            # Costruisce la transazione di approve
            amount_to_approve = 2**256 - 1 # Infinite approval
            nonce = w3.eth.get_transaction_count(wallet_addr)
            
            tx = contract.functions.approve(lp_addr, amount_to_approve).build_transaction({
                'from': wallet_addr,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'chainId': config.CHAIN_ID
            })

            signed_tx = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            log.info(f"✅ Transazione di Approve inviata! Hash: {w3.to_hex(tx_hash)}")
            log.info("Attendi la conferma sulla blockchain.")
        else:
            log.info(f"✅ Allowance OK: {allowance / (10**decimals):.2f} USDT autorizzati per Azuro V3.")

    except Exception as e:
        log.error(f"Errore nel setup del wallet: {e}")

if __name__ == "__main__":
    setup_wallet()
