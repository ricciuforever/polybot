import requests

rpcs = [
    "https://polygon-mainnet.public.blastapi.io",
    "https://rpc.ankr.com/polygon",
    "https://1rpc.io/matic",
    "https://polygon.llamarpc.com",
    "https://rpc-mainnet.maticvigil.com"
]

def test():
    print("=== TESTING POLYGON RPC CONNECTIVITY ===\n")
    for rpc in rpcs:
        print(f"Testing {rpc}...")
        try:
            payload = {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}
            resp = requests.post(rpc, json=payload, timeout=5)
            if resp.status_code == 200:
                print(f"✅ Success! Block Number: {int(resp.json()['result'], 16)}")
            else:
                print(f"❌ Failed: Status {resp.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    test()
