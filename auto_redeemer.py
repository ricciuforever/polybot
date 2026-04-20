import time
import asyncio
from poly_trader import PolyTrader
from modules.logger import get_logger

log = get_logger("auto_redeemer")

def run_redeemer():
    log.info("Avvio Auto-Redeemer (Processo Separato)")
    trader = PolyTrader()

    # Eseguiamo in un loop continuo
    while True:
        try:
            log.info("💰 Avvio scansione auto-redeem indipendente...")
            redeemed = trader.auto_redeem()
            if redeemed and redeemed > 0:
                log.info(f"💰 ✅ Auto-Redeemer: Riscattate {redeemed} posizioni con successo!")
            else:
                log.debug("Auto-Redeemer: Nessuna posizione da riscattare o nessun nuovo riscatto effettuato.")
        except Exception as e:
            log.error(f"❌ Errore critico nel processo di auto-redeem: {e}")

        # Pausa di 5 minuti (300 secondi)
        time.sleep(30)

if __name__ == "__main__":
    run_redeemer()
