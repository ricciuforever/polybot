import requests
import json
resp = requests.get("https://gamma-api.polymarket.com/markets?limit=1&closed=true")
data = resp.json()
print(json.dumps(data[0], indent=2))
