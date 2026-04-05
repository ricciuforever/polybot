import time
import config
from azuro_trader import AzuroTrader
from modules.azuro_watcher import AzuroWatcher
from modules.logger import get_logger

log = get_logger("dry_run")

def run_test():
    log.info("=== AVVIO AZURO DRY-RUN TEST ===")
    
    # 1. Inizializzazione
    trader = AzuroTrader()
    watcher = AzuroWatcher()
    
    # 2. Controllo Connessione
    ok, msg = trader.check_connection()
    if not ok:
        log.error(f"Errore connessione: {msg}")
        return
        
    # 3. Scoperta Mercato
    log.info("Ricerca mercato BTC attivo su Azuro...")
    market = watcher.find_btc_market()
    
    if not market:
        log.warning("Nessun mercato reale trovato ora. Uso dati di simulazione.")
        market = {
            "conditionId": 1234567890,
            "title": "BTC Price @ NEXT WINDOW (SIMULATED)",
            "outcomes": {"10001": 1.95, "10002": 1.91}
        }

    # 4. Strategia (Simulata)
    # Supponiamo un segnale BUY_UP (Outcome 10001)
    action = "BUY_UP"
    outcome_id = 10001
    odds = market['outcomes'].get(str(outcome_id), 1.5)
    
    log.info(f"Dati Mercato: {market['title']} | ID: {market['conditionId']}")
    log.info(f"Azione simulata: {action} on Outcome {outcome_id} @ Odds {odds}")
    
    # 5. Esecuzione (DRY-RUN)
    if config.DRY_RUN:
        log.info(f"🚀 [DRY-RUN] Simulo lp.bet() su Azuro V3...")
        log.info(f"Parametri: Core={config.AZURO_CORE} | Amount={config.BET_SIZE} USDT")
        log.info(f"Target: Condition {market['conditionId']} | Outcome {outcome_id} | MinOdds {odds}")
        log.info("✅ Test DRY-RUN completato con successo (Nessuna transazione inviata).")
    else:
        log.warning("ATTENZIONE: DRY_RUN è impostato su FALSE. Questo script nel loop reale piazzerà scommesse vere.")

if __name__ == "__main__":
    run_test()
