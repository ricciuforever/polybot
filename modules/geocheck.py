"""
modules/geocheck.py — Verifica che l'IP corrente non sia bloccato da Polymarket.
Lancia RuntimeError se bloccato. Va chiamato all'avvio del bot.
"""
import requests
import config
from modules.logger import get_logger

log = get_logger("geocheck")


def check() -> dict:
    """
    Chiama l'endpoint geoblock di Polymarket.
    Ritorna il dict {"blocked": bool, "ip": str, "country": str, ...}
    Lancia RuntimeError se bloccato.
    """
    try:
        resp = requests.get(config.GEOBLOCK_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"[GeoCheck] Impossibile contattare geoblock endpoint: {e}")

    ip      = data.get("ip", "?")
    country = data.get("country", "?")
    blocked = data.get("blocked", True)

    if blocked:
        raise RuntimeError(
            f"[GeoCheck] IP BLOCCATO! IP={ip}, Country={country}. "
            f"Assicurati che la VPN NordVPN con server Ireland sia attiva."
        )

    log.info(f"GeoCheck OK — IP={ip}, Country={country} (non bloccato)")
    return data
