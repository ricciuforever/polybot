import requests
import json

URL = "https://api.onchainfeed.org/api/v1/public/gateway/graphql"

query = """
query {
  games(
    where: { 
      status: Created,
      OR: [
        { title_contains: "Bitcoin" },
        { title_contains: "BTC" }
      ]
    }
  ) {
    id
    title
    startsAt
    conditions {
      conditionId
      status
      coreAddress
      outcomes {
        outcomeId
        currentOdds
      }
    }
  }
}
"""

r = requests.post(URL, json={'query': query})
print(json.dumps(r.json(), indent=2))
