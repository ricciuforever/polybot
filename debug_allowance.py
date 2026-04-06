import requests
from web3 import Web3
import config

RPC_URLS = ["https://1rpc.io/matic", "https://polygon-rpc.com"]
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
# Polymarket CTF Exchange (Polygon)
CTF_EXCHANGE = "0x4D970805f78A966f121DC7FA03bcB21128F75C8c"

def check():
    w3 = Web3(Web3.HTTPProvider(RPC_URLS[0]))
    addr = config.POLY_PROXY_ADDRESS or "0x..." # EOA if no proxy
    if addr == "0x...":
        from eth_account import Account
        addr = Account.from_key(config.PRIVATE_KEY).address

    print(f"Checking address: {addr}")
    
    # USDC ABI Snippet
    abi = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
    ]
    
    usdc = w3.eth.contract(address=USDC_E, abi=abi)
    balance = usdc.functions.balanceOf(addr).call()
    allowance = usdc.functions.allowance(addr, CTF_EXCHANGE).call()
    
    print(f"USDC Balance: {balance / 1e6} USDC")
    print(f"USDC Allowance for CTF: {allowance / 1e6} USDC")
    
    if allowance < 100 * 1e6:
        print("!!! Allowance is low. You might need to approve USDC for Polymarket.")

if __name__ == "__main__":
    check()
