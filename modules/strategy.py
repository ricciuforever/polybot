import config
from modules.logger import get_logger

log = get_logger("strategy")

BUY_UP   = "BUY_UP"
BUY_DOWN = "BUY_DOWN"
HOLD     = "HOLD"

def evaluate(
    asset: str,
    movement_pct: float,
    up_price: float | None,
    down_price: float | None,
    time_left: int,
    trend_direction: int,
    threshold: float
) -> tuple[str, float]:
    """
    Valuta e ritorna (azione, confidence).
    Include filtri di tempo (time_left), trend (trend_direction) e soglie dinamiche.
    """
    max_price = config.BUY_MAX_PRICE

    if up_price is None or down_price is None:
        return HOLD, 0.0

    # --- 1. FILTRO TEMPO (Time-in-Bucket) ---
    if time_left > 270:
        log.debug(f"[{asset}] Troppo presto ({time_left}s rimanenti) — HOLD")
        return HOLD, 0.0
    if time_left < 20:
        log.debug(f"[{asset}] Troppo tardi ({time_left}s rimanenti) — HOLD")
        return HOLD, 0.0

    # --- 2. FILTRO MOVIMENTO ---
    if abs(movement_pct) < threshold:
        log.debug(f"[{asset}] Movimento {movement_pct:+.4f}% sotto soglia {threshold}% — HOLD")
        return HOLD, 0.0

    confidence = min(abs(movement_pct) / threshold, 1.0) if threshold > 0 else 1.0

    # --- 3. FILTRO TREND E SEGNALE ---
    if movement_pct > 0:
        if trend_direction < 0:
            log.debug(f"[{asset}] Segnale UP (+{movement_pct:.4f}%) ma trend a 5m DOWN — HOLD")
            return HOLD, 0.0
        if up_price < max_price:
            log.info(
                f"[{asset}] SEGNALE BUY_UP — {movement_pct:+.4f}% | "
                f"Up={up_price:.3f} < MAX={max_price} | conf={confidence:.2f} | time_left={time_left}s"
            )
            return BUY_UP, confidence
        log.debug(f"[{asset}] Up price {up_price:.3f} >= MAX {max_price} — HOLD")
        return HOLD, 0.0
    else:
        if trend_direction > 0:
            log.debug(f"[{asset}] Segnale DOWN ({movement_pct:.4f}%) ma trend a 5m UP — HOLD")
            return HOLD, 0.0
        if down_price < max_price:
            log.info(
                f"[{asset}] SEGNALE BUY_DOWN — {movement_pct:+.4f}% | "
                f"Down={down_price:.3f} < MAX={max_price} | conf={confidence:.2f} | time_left={time_left}s"
            )
            return BUY_DOWN, confidence
        log.debug(f"[{asset}] Down price {down_price:.3f} >= MAX {max_price} — HOLD")
        return HOLD, 0.0
