import logging
import json
import time
from poly_trader import PolyTrader
import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("liquidator")

def sell_all():
    trader = PolyTrader()
    log.info("🚀 Avvio Liquidazione di Emergenza...")
    
    # Recupera le posizioni
    positions = trader.get_positions()
    if not positions:
        log.info("Nessuna posizione attiva trovata da vendere.")
        return

    for p in positions:
        title = p['title']
        size = p['size']
        # Su Polymarket, per vendere si usa l'azione SELL con lo stesso token_id
        # Per semplicità qui identifichiamo il token e vendiamo
        log.info(f"VENDITA: {title} | Size: {size}")
        
        # Nota: La funzione execute_market_trade va adattata o usata con size negativa se supportato, 
        # oppure chiamiamo direttamente il client per un ordine di SELL.
        try:
            # Recuperiamo il token_id corretto (YES o NO) cercando di nuovo il mercato
            # Ma più velocemente, usiamo le info della Data API se disponibili
            # In questo script di emergenza, tentiamo la vendita tramite il client CLOB
            # Dobbiamo trovare il token_id associato alla posizione
            pass
            # Lo script completo richiede di mappare di nuovo il condition_id al token_id
        except Exception as e:
            log.error(f"Errore vendita {title}: {e}")

if __name__ == "__main__":
    # Invece di uno script parziale, usiamo una logica di vendita diretta nel trader
    # Procedo a modificare poly_trader per includere una funzione sell_all_positions
    pass
