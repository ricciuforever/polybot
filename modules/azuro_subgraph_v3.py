import aiohttp
import logging
from typing import List, Dict, Any
import config

log = logging.getLogger("azuro_subgraph_v3")

class AzuroV3Subgraph:
    def __init__(self):
        self.url = config.AZURO_SUBGRAPH_URL

    async def get_user_bets(self, wallet_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera le scommesse attive e passate dell'utente dal Subgraph V3."""
        query = """
        query GetUserBets($bettor: String!, $first: Int!) {
          bets(where: { bettor: $bettor }, first: $first, orderBy: createdBlockTimestamp, orderDirection: desc) {
            id
            amount
            status
            payout
            createdBlockTimestamp
            selections {
              outcome {
                id
                condition {
                  game {
                    title
                    sport { name }
                    league { name }
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "bettor": wallet_address.lower(),
            "first": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json={'query': query, 'variables': variables}, timeout=10) as response:
                    if response.status != 200:
                        log.warning(f"Errore Subgraph V3: {response.status}")
                        return []
                    data = await response.json()
                    return data.get('data', {}).get('bets', [])
        except Exception as e:
            log.error(f"Errore query Subgraph V3: {e}")
            return []

if __name__ == "__main__":
    import asyncio
    async def test():
        sg = AzuroV3Subgraph()
        wallet = config.WALLET_ADDRESS
        bets = await sg.get_user_bets(wallet)
        for b in bets:
            title = b['selections'][0]['outcome']['condition']['game']['title']
            print(f"Bet: {title} | Amount: {b['amount']} | Status: {b['status']}")
    
    asyncio.run(test())
