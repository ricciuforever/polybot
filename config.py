"""
config.py — Carica e valida tutte le variabili d'ambiente.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Credenziali Azuro / Wallet ---
PRIVATE_KEY     = os.getenv("PRIVATE_KEY", "").strip()
if PRIVATE_KEY and not PRIVATE_KEY.startswith("0x"):
    PRIVATE_KEY = "0x" + PRIVATE_KEY

WALLET_ADDRESS  = os.getenv("WALLET_ADDRESS", "").strip()
AZURO_LP        = os.getenv("AZURO_LP_CONTRACT", "0x204e7371Ade792c5C006fb52711c50a7efC843ed").strip()
AZURO_CORE      = os.getenv("AZURO_CORE_CONTRACT", "0x7bB7d025170dcb06573D5514fC7eBEa5DE794017").strip()
AZURO_TOKEN     = os.getenv("USDT_ADDRESS", "0xc2132D05D31c914a87C6611C10748AEb04B58e8F").strip()
AZURO_RPC       = os.getenv("POLYGON_RPC", "https://1rpc.io/matic").strip()
# Fallback se l'RPC pubblico è saturo o down
if AZURO_RPC == "https://polygon-rpc.com":
    AZURO_RPC = "https://1rpc.io/matic"
AZURO_SUBGRAPH  = "https://thegraph.azuro.org/v3/polygon"

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
BET_SIZE        = float(os.getenv("BET_SIZE", "2.0"))            # Stake per ordine (USDT/USDC)
DRY_RUN         = os.getenv("DRY_RUN", "True").lower() != "false"
LOOP_INTERVAL   = int(os.getenv("LOOP_INTERVAL", "5"))           # secondi tra cicli
ENABLE_REDEEM   = False  # DISATTIVATO PER BAN RELAYER
AZURO_MODE      = True   # Forza l'utilizzo di Azuro

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
