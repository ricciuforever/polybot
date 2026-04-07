import asyncio
import time
import json
import logging
from web3 import AsyncWeb3
import aiohttp
from typing import Dict, Any, List

import config
from modules.azuro_subgraph import AzuroMarketsWatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-8s] %(name)s — %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("async_main")

SIGNER_URL = "http://localhost:3000/sign"

class AsyncAzuroBot:
    def __init__(self):
        # We assume RPC is working optimally with AsyncWeb3 (e.g. Infura WSS or reliable HTTP)
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(config.AZURO_RPC))
        self.subgraph = AzuroMarketsWatcher(config.ASSETS)
        self.prices = {} # Cache for Binance
        self.running = True
        self.session = None

    async def connect_binance(self):
        """WebSockets to track Binance futures directly without blocking"""
        import websockets
        uri = "wss://fstream.binance.com/stream?streams=" + "/".join([f"{a.lower()}usdt@markPrice" for a in config.ASSETS])
        
        while self.running:
            try:
                async with websockets.connect(uri) as ws:
                    log.info("🟢 Connesso al WebSocket Binance Futures")
                    async for message in ws:
                        if not self.running: break
                        data = json.loads(message)
                        if 'data' in data:
                            sym = data['data']['s'].replace("USDT", "")
                            if sym in config.ASSETS:
                                self.prices[sym] = float(data['data']['p'])
            except Exception as e:
                log.warning(f"Binance WS ricollegamento: {e}")
                await asyncio.sleep(2)

    async def get_signature_from_node(self, target_core: str, amount_raw: int, expires_at: int, 
                                      condition_id: str, outcome_id: int, min_odds: int):
        """Asks the local Node.js microservice to natively sign the EIP-712 payload."""
        client_data = {
            "attention": "DGPredict",
            "affiliate": "0x0000000000000000000000000000000000000000",
            "core": target_core,
            "expiresAt": expires_at,
            "chainId": config.AZURO_CHAIN_ID,
            "relayerFeeAmount": 0
        }
        
        payload = {
            "privateKey": config.PRIVATE_KEY,
            "clientData": client_data,
            "bet": {
                "conditionId": condition_id,
                "outcomeId": outcome_id,
                "minOdds": min_odds,
                "amount": amount_raw,
                "nonce": int(time.time() * 1000)
            }
        }
        
        try:
            async with self.session.post(SIGNER_URL, json=payload) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return data.get('signature')
                else:
                    log.error(f"Signer Service Error: {data}")
                    return None
        except Exception as e:
            log.error(f"Cannot reach Singer Service at {SIGNER_URL}: {e}")
            return None

    async def place_live_bet(self, game: Dict[str, Any], direction: str):
        """Uses the Node.js signature to place the bet asynchronously"""
        target_core = game.get("coreAddress")
        if not target_core:
            target_core = config.AZURO_CORE
            
        condition_id = game["conditionId"]
        
        # UP = outcome 1, DOWN = outcome 2 (varies per environment, using 1 and 2 for sample)
        outcome_id = 1 if direction == "UP" else 2 
        
        amount_human = config.BET_SIZE
        amount_raw = int(amount_human * 1_000_000)
        min_odds_raw = int(config.MIN_ODDS * 1_000_000_000_000)
        expires_at = int(time.time()) + 300
        nonce = int(time.time() * 1000)
        
        signature = await self.get_signature_from_node(target_core, amount_raw, expires_at, condition_id, outcome_id, min_odds_raw)
        if not signature:
            log.error(f"Failed to obtain signature for {game['name']}. Aborting bet.")
            return

        api_bet_payload = {
            "clientData": {
                "attention": "DGPredict",
                "affiliate": "0x0000000000000000000000000000000000000000",
                "core": target_core,
                "expiresAt": expires_at,
                "chainId": config.AZURO_CHAIN_ID,
                "relayerFeeAmount": "0",
                "isFeeSponsored": False,
                "isBetSponsored": False,
                "isSponsoredBetReturnable": False
            },
            "bet": {
                "conditionId": condition_id,
                "outcomeId": outcome_id,
                "minOdds": str(min_odds_raw),
                "amount": str(amount_raw),
                "nonce": str(nonce)
            }
        }
        
        wallet_addr = config.WALLET_ADDRESS.lower()
        payload = {
            "environment": config.AZURO_ENVIRONMENT,
            "bettor": wallet_addr,
            "betOwner": wallet_addr,
            "clientBetData": api_bet_payload,
            "bettorSignature": signature
        }
        
        api_url = f"{config.AZURO_API_URL}/bet/orders/ordinar"
        log.info(f"Invio ordine LIVE Relayer Async per {game['name']}... | Core: {target_core}")
        
        try:
            async with self.session.post(api_url, json=payload, timeout=10) as resp:
                resp_data = await resp.json()
                if resp.status in [200, 201]:
                    log.info(f"✅ Ordine accettato: {resp_data.get('id')}")
                else:
                    log.error(f"❌ Fallimento Bet {game['asset']}: {resp.status} {resp_data}")
        except asyncio.TimeoutError:
             log.error("❌ Fallimento Bet: Timeout TheRelayer")

    async def trading_loop(self):
        """Asynchronous market observation and execution"""
        while self.running:
            # Get latest games from the Graph
            games = await self.subgraph.get_imminent_matches(limit=10)
            if games:
                log.info(f"Trovati {len(games)} mercati imminenti")
                for game in games:
                    asset = game["asset"]
                    price = self.prices.get(asset)
                    # Fake simplistic strategy based on active price threshold mapping
                    direction = "UP"  # Replace with moving average / logic
                    log.info(f"Segnale mock: {direction} su {game['name']} | Prezzo Attuale: {price}")
                    
                    if not config.DRY_RUN:
                        # Fires the bet asynchronously without halting the loop! (Fire and forget or gather)
                        asyncio.create_task(self.place_live_bet(game, direction))
            else:
                log.info("Nessun mercato compatibile trovato nel Subgraph.")
            
            await asyncio.sleep(config.LOOP_INTERVAL)

    async def run(self):
        if not await self.w3.is_connected():
            log.error("RPC Asincrono non raggiungibile")
            return
            
        log.info(f"Azuro Async Sniper V4 avviato.")
        self.session = aiohttp.ClientSession()
        
        # Run binance and trading concurrently
        try:
            await asyncio.gather(
                self.connect_binance(),
                self.trading_loop()
            )
        finally:
            self.running = False
            await self.session.close()

if __name__ == "__main__":
    bot = AsyncAzuroBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        log.info("Chiusura...")
