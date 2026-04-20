import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

DRY_RUN = False

# Configurazione Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash') # Uso modello stabile 2.0 Flash

PRIVATE_KEY = os.getenv("PRIVATE_KEY", "").strip()
if PRIVATE_KEY and not PRIVATE_KEY.startswith("0x"): PRIVATE_KEY = "0x" + PRIVATE_KEY
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0x27Fb2C57b1149bE45d99070a906753D5A8ad6e3a").strip()
SAFE_ADDRESS = os.getenv("SAFE_ADDRESS", "0xf70ce42b1bbebcc1deee5315506373ba7e535e9d").strip()

# Polymarket API & Builder (Nuove chiavi)
POLY_API_KEY = os.getenv("POLY_API_KEY", "").strip()
POLY_BUILDER_ID = os.getenv("POLY_BUILDER_ID", "").strip()
POLY_RELAYER_KEY = os.getenv("POLY_RELAYER_KEY", "").strip()
POLY_RELAYER_ADDRESS = os.getenv("WALLET_ADDRESS", "0x27Fb2C57b1149bE45d99070a906753D5A8ad6e3a").strip()

# Source IP Binding (es. IP Finlandia da Plesk)
BIND_IP = os.getenv("BIND_IP", "").strip()


# --- POLYMARKET CONFIG ---
POLY_CLOB_URL = "https://clob.polymarket.com"
POLY_GAMMA_URL = "https://gamma-api.polymarket.com"

# Contratti Polymarket (Polygon)
POLY_USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
POLY_CTF = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
POLY_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

# Gestione RPC con Fallback (ChainList)
RPC_NODES = [
    "https://polygon-public.nodies.app",
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.llamarpc.com",
    "https://rpc-mainnet.matic.quiknode.pro",
    "https://1rpc.io/matic"
]
POLY_RPC = RPC_NODES[1] # publicnode
# Asset da monitorare per Prezzi e Mercati (SOLO CRYPTO)
ASSETS = ["BTC", "ETH", "SOL", "XRP", "DOGE"]
DRY_RUN = False # TORNIAMO LIVE
BET_SIZE = 1.10
COOLDOWN_SECONDS = 300 # Attesa di 5 minuti tra scommesse sullo stesso asset
# Soglie conservative
THRESHOLDS = {
    "BTC": 0.08,
    "ETH": 0.08
}

ONLY_SHORT_INTERVALS = True # Cerca solo mercati con intervalli (es. 5-15 min)

WINDOW_SECONDS = 60    # Finestra per il calcolo del movimento
MIN_ODDS = 1.80
BET_SIZE = 1.10 # 1.10 USDC.e (per superare il minimo di 1$ del CLOB)
LOOP_INTERVAL = 5
CHAIN_ID = 137

def validate():
    if not DRY_RUN and (not PRIVATE_KEY or not WALLET_ADDRESS):
        raise EnvironmentError("Mancano credenziali nel .env")
TAKE_PROFIT_THRESHOLD = 0.25 # 20c profitto su singola posizione per triggerare la vendita
