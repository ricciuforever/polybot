import requests
import json

BASE_URL = "https://api.onchainfeed.org/api/v1/public"

def check_envs():
    print("=== CHECK ENVIRONMENTS ===")
    url = f"{BASE_URL}/market-manager/environments"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            envs = resp.json()
            print(json.dumps(envs, indent=2))
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_envs()
