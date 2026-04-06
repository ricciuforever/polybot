import requests
import json
import config

def diagnostic():
    print(f"=== DIAGNOSTIC RPC: {config.AZURO_RPC[:40]}... ===\n")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_chainId",
        "params": [],
        "id": 1
    }
    
    headers = {
        "Origin": "https://dgpredict.com",
        "Referer": "https://dgpredict.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.post(config.AZURO_RPC, json=payload, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        if resp.status_code == 200:
            result = resp.json().get('result')
            if result:
                print(f"✅ Connection OK! Chain ID (hex): {result}")
            else:
                print("❌ No result in JSON response.")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    diagnostic()
