import requests
from web3 import Web3
import os
import config

def test_connectivity():
    print(f"--- TESTING AZURO CONNECTIVITY ---")
    
    # 1. Test RPC
    rpc = config.AZURO_RPC
    print(f"Testing RPC: {rpc}")
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 20}))
    try:
        is_connected = w3.is_connected()
        print(f"RPC Connected: {is_connected}")
        if is_connected:
            print(f"Chain ID: {w3.eth.chain_id}")
            print(f"Latest Block: {w3.eth.block_number}")
    except Exception as e:
        print(f"RPC Error: {e}")

    # 2. Test Subgraph
    subgraph = config.AZURO_SUBGRAPH
    print(f"\nTesting Subgraph: {subgraph}")
    try:
        query = "{ _meta { block { number } } }"
        resp = requests.post(subgraph, json={'query': query}, timeout=15)
        print(f"Subgraph Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Subgraph Meta: {resp.json()}")
    except Exception as e:
        print(f"Subgraph Error: {e}")

if __name__ == "__main__":
    test_connectivity()
