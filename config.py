"""
config.py — Carica e valida tutte le variabili d'ambiente.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Credenziali Polymarket ---
POLY_API_KEY    = os.getenv("POLY_API_KEY", "")
POLY_SECRET     = os.getenv("POLY_SECRET", "")
POLY_PASSPHRASE = os.getenv("POLY_PASSPHRASE", "")
PRIVATE_KEY     = os.getenv("HOT_WALLET_PRIVATE_KEY", "")
POLY_PROXY_ADDRESS = os.getenv("POLY_PROXY_ADDRESS", "")
RELAYER_API_KEY    = os.getenv("RELAYER_API_KEY", "")
RELAYER_API_KEY_ADDRESS = os.getenv("RELAYER_API_KEY_ADDRESS", "")

# --- Endpoint API ---
CLOB_URL    = "https://clob.polymarket.com"
GAMMA_URL   = "https://gamma-api.polymarket.com"
GEOBLOCK_URL = "https://polymarket.com/api/geoblock"

# --- Strategia Multi-Asset ---
ASSETS = ["BTC", "ETH", "SOL", "XRP", "DOGE"]

# Soglie di attivazione personalizzate per asset (le altcoin sono più volatili)
THRESHOLDS = {
    "BTC": 0.03,
    "ETH": 0.04,
    "XRP": 0.05,
    "SOL": 0.06,
    "DOGE": 0.08
}

WINDOW_SECONDS  = int(os.getenv("WINDOW_SECONDS", "60"))         # finestra sliding
BUY_MAX_PRICE   = float(os.getenv("BUY_MAX_PRICE", "0.55"))      # max prezzo acquisto
BET_SIZE        = float(os.getenv("BET_SIZE", "2"))              # USDC per ordine
DRY_RUN         = os.getenv("DRY_RUN", "True").lower() != "false"
LOOP_INTERVAL   = int(os.getenv("LOOP_INTERVAL", "5"))           # secondi tra cicli

# --- AI (Gemini) ---
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
ENABLE_AI_VETO      = False
AI_MIN_CONFIDENCE   = float(os.getenv("AI_MIN_CONFIDENCE", "0.75"))

# Polygon Chain ID
CHAIN_ID = 137

def validate():
    """Verifica che le credenziali obbligatorie siano presenti."""
    missing = []
    if not DRY_RUN:
        if not POLY_API_KEY:   missing.append("POLY_API_KEY")
        if not POLY_SECRET:    missing.append("POLY_SECRET")
        if not POLY_PASSPHRASE: missing.append("POLY_PASSPHRASE")
        if not PRIVATE_KEY or PRIVATE_KEY == "0x...":
            missing.append("HOT_WALLET_PRIVATE_KEY")
    if missing:
        raise EnvironmentError(
            f"[CONFIG] Credenziali mancanti nel .env: {', '.join(missing)}"
        )
