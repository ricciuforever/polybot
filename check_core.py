import requests
import json

ENDPOINTS = [
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3",
    "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon"
]
CORE = "0x7bb7d025170dcb06573d5514fc7ebea5de794017"

query = """
{
  conditions(where: { coreAddress: "%s" }, first: 5) {
    conditionId
    game { title }
  }
}
""" % CORE

for url in ENDPOINTS:
    print(f"Testing {url}...")
    r = requests.post(url, json={'query': query})
    print(json.dumps(r.json(), indent=2))
