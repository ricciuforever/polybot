import config
from modules.logger import get_logger
log = get_logger("strategy")

HOLD, BUY_UP, BUY_DOWN = "HOLD", "BUY_UP", "BUY_DOWN"

def evaluate(asset, movement_pct, up_odds, down_odds, time_left, trend, threshold):
    min_odds = config.MIN_ODDS
    
    if abs(movement_pct) < threshold:
        return HOLD, 0.0

    confidence = min(abs(movement_pct) / (threshold * 2), 1.0)

    if movement_pct > 0: # Trend salita
        if up_odds >= min_odds:
            log.info(f"📈 Segnale UP: Mov {movement_pct:+.4f}% | Quota {up_odds:.2f}")
            return BUY_UP, confidence
    else: # Trend discesa
        if down_odds >= min_odds:
            log.info(f"📉 Segnale DOWN: Mov {movement_pct:+.4f}% | Quota {down_odds:.2f}")
            return BUY_DOWN, confidence

    return HOLD, 0.0