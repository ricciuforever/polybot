import asyncio
import time
import json
import os
from modules.azuro_live_watcher import AzuroLiveWatcher
from modules.ai_agent import AIAgent
from modules.azuro_subgraph_v3 import AzuroV3Subgraph
from azuro_trader import AzuroTrader
import config
from modules.logger import get_logger
from decimal import Decimal

log = get_logger("bot_live")

class NitroBotLive:
    def __init__(self):
        self.watcher = AzuroLiveWatcher()
        self.ai = AIAgent()
        self.subgraph = AzuroV3Subgraph()
        self.trader = AzuroTrader()
        self.running = True
        self.confidence_threshold = 0.75
        self.bet_size = float(config.BET_SIZE)
        self.processed_games = set()
        self.state_file = "bot_state.json"
        self.state = {
            "last_update": 0,
            "live_games": [],
            "ai_logs": [],
            "wallet": {"pol": 0, "usdc": 0, "address": config.WALLET_ADDRESS},
            "stats": {"total_bets": 0, "won_bets": 0}
        }

    async def run(self):
        log.info("🚀 NitroBot Live Betting Avviato!")
        log.info(f"Parametri: BetSize={self.bet_size} USDT | Threshold={self.confidence_threshold}")
        
        while self.running:
            try:
                # 1. Recupero Match Live
                live_games = await self.watcher.get_live_games()
                
                # 2. Recupero Saldi e Scommesse Utente (Subgraph V3)
                pol, usdt = await self.trader.get_balances()
                user_bets = await self.subgraph.get_user_bets(config.WALLET_ADDRESS)
                
                # Aggiornamento stato per la Dashboard
                self.state["live_games"] = live_games
                self.state["wallet"] = {
                    "pol": float(pol),
                    "usdc": float(usdt),
                    "address": config.WALLET_ADDRESS
                }
                self.state["stats"]["total_bets"] = len(user_bets)
                self.state["last_update"] = int(time.time())
                
                # Analisi e Trading per ogni match
                for game in live_games:
                    game_id = game['gameId']
                    if game_id in self.processed_games: continue
                    
                    log.info(f"🧐 Analisi: {game['title']} ({game['sport']})")
                    analysis = await self.ai.analyze_match(game)
                    
                    confidence = analysis.get('confidence', 0)
                    outcome_id = analysis.get('outcomeId')
                    
                    # Log AI
                    ai_log = {
                        "time": int(time.time()),
                        "match": game['title'],
                        "confidence": confidence,
                        "recommendation": analysis.get('recommendation'),
                        "decision": "Bet" if (confidence >= self.confidence_threshold and outcome_id) else "Skip"
                    }
                    self.state["ai_logs"] = [ai_log] + self.state["ai_logs"][:19]
                    
                    if confidence >= self.confidence_threshold and outcome_id:
                        log.info(f"🔥 SEGNALE: {analysis.get('recommendation')}")
                        if not config.DRY_RUN:
                            chosen_outcome = next((o for o in game['outcomes'] if o['outcomeId'] == outcome_id), None)
                            if chosen_outcome:
                                success, tx = self.trader.execute_bet(game['conditionId'], outcome_id, self.bet_size, chosen_outcome['odds'])
                                if success:
                                    self.processed_games.add(game_id)
                                    log.info(f"✅ Bet OK: {tx}")
                                else:
                                    log.error(f"❌ Bet Fallita: {tx}")
                    else:
                        log.info(f"⏸️ No Value ({int(confidence*100)}%)")
                
                with open(self.state_file, "w") as f:
                    json.dump(self.state, f, indent=2)
                    
            except Exception as e:
                log.error(f"Errore loop: {e}")
            
            await asyncio.sleep(30)

if __name__ == "__main__":
    bot = NitroBotLive()
    asyncio.run(bot.run())
