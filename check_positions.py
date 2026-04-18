import sys, requests
sys.path.insert(0, ".")
from web3 import Web3
import config

w3 = Web3(Web3.HTTPProvider(config.AZURO_RPC))
from eth_account import Account
account = Account.from_key(config.PRIVATE_KEY)
my_addr = account.address

# ConditionId del mercato 7:15-7:20PM (DOWN ha vinto)
cond_id = "0x8331818669dedc7ffca0646dd132f70859e9b0adcdef1a353dd6f02419d3acaf"
cond_bytes = bytes.fromhex(cond_id[2:])
parent = b'\x00' * 32
usdc = Web3.to_checksum_address(config.POLY_USDC)

# NegRiskAdapter e CTF addresses da Polymarket
CTF_EXCHANGE = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"  # Conditional Tokens
NEG_RISK_CTF_EXCHANGE = "0xC5d563A36AE78145C45a50134d48A1215220f80a"  # NegRisk CTF Exchange
NEG_RISK_ADAPTER = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"  # NegRisk Adapter

# redeemPositions ABI
redeem_abi = [{
    "inputs": [
        {"name": "collateralToken", "type": "address"},
        {"name": "parentCollectionId", "type": "bytes32"},
        {"name": "conditionId", "type": "bytes32"},
        {"name": "indexSets", "type": "uint256[]"}
    ],
    "name": "redeemPositions",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

# Prova su tutti i contratti
for name, addr in [("CTF", CTF_EXCHANGE), ("NegRisk CTF", NEG_RISK_CTF_EXCHANGE)]:
    print(f"\n=== Tentativo {name} ({addr[:10]}...) ===")
    try:
        ctf = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=redeem_abi)
        tx = ctf.functions.redeemPositions(
            usdc, parent, cond_bytes, [1, 2]
        ).build_transaction({
            'from': my_addr,
            'nonce': w3.eth.get_transaction_count(my_addr),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        signed = w3.eth.account.sign_transaction(tx, config.PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"TX inviata: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        print(f"Status: {'✅ SUCCESS' if receipt.status == 1 else '❌ FAILED'}")
        print(f"Gas: {receipt.gasUsed}")
        if receipt.status == 1:
            break
    except Exception as e:
        err = str(e)
        if "execution reverted" in err:
            print(f"Reverted - probabilmente non su questo contratto")
        else:
            print(f"Errore: {err[:150]}")
