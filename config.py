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
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "").strip()
SAFE_ADDRESS = os.getenv("SAFE_ADDRESS", "0xF70ce42B1bBEbCc1deEe5315506373Ba7E535e9d").strip()

# Azuro V3 (Polygon) - MAINNET Configuration
AZURO_TOKEN = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"      # USDT su Polygon
AZURO_LP = "0x0FA7FB5407eA971694652E6E16C12A52625DE1b8"         # Pool USDT Production
AZURO_CORE = "0xF9548Be470A4e130c90ceA8b179FCD66D2972AC7"       # Core USDT Production
AZURO_RELAYER = "0x8dA05c0021e6b35865FDC959c54dCeF3A4AbBa9d"    # Relayer USDT Production

# --- POLYMARKET CONFIG ---
POLY_CLOB_URL = "https://clob.polymarket.com"
POLY_GAMMA_URL = "https://gamma-api.polymarket.com"

# Contratti Polymarket (Polygon)
POLY_USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
POLY_CTF = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
POLY_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

# --- AZURO CONFIG (Legacy/Fallback) ---
AZURO_API_URL = "https://api.onchainfeed.org/api/v1/public"
AZURO_REST_API = "https://api.onchainfeed.org/api/v1/public"
AZURO_ENVIRONMENT = "PolygonUSDT" 
AZURO_PROXY = "0x7043a1215b248a329df05b5cd4da075f70a1a5b4"

# Gestione RPC con Fallback (ChainList)
RPC_NODES = [
    "https://polygon-public.nodies.app",
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.llamarpc.com",
    "https://rpc-mainnet.matic.quiknode.pro",
    "https://1rpc.io/matic"
]
AZURO_RPC = RPC_NODES[0] # Default
AZURO_CHAIN_ID = 137

# Subgraphs Azuro V3
# Client: Per scommesse utente e storia
AZURO_SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
# Data-Feed: Per quote e match live (Unfiltered)
AZURO_DATA_FEED_URL = "https://thegraph.onchainfeed.org/subgraphs/name/azuro-protocol/azuro-data-feed-polygon-v3"

# Asset da monitorare per Prezzi e Mercati (SOLO CRYPTO)
ASSETS = ["BTC", "ETH", "XRP", "SOL", "DOGE"]
DRY_RUN = False # TORNIAMO LIVE
BET_SIZE = 1.10
COOLDOWN_SECONDS = 300 # Attesa di 5 minuti tra scommesse sullo stesso asset
# Soglie conservative
THRESHOLDS = {
    "BTC": 0.08,
    "ETH": 0.10,
    "XRP": 0.15,
    "SOL": 0.15,
    "DOGE": 0.20
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