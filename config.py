import os
from dotenv import load_dotenv
load_dotenv()

DRY_RUN = False

PRIVATE_KEY = os.getenv("PRIVATE_KEY", "").strip()
if PRIVATE_KEY and not PRIVATE_KEY.startswith("0x"): PRIVATE_KEY = "0x" + PRIVATE_KEY
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "").strip()
SAFE_ADDRESS = os.getenv("SAFE_ADDRESS", "0xF70ce42B1bBEbCc1deEe5315506373Ba7E535e9d").strip()

# Azuro V3 (Polygon) - MAINNET Configuration
AZURO_TOKEN = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"      # USDT su Polygon
AZURO_LP = "0x0FA7FB5407eA971694652E6E16C12A52625DE1b8"         # Pool USDT Production
AZURO_CORE = "0xF9548Be470A4e130c90ceA8b179FCD66D2972AC7"       # Core USDT Production
AZURO_RELAYER = "0x8dA05c0021e6b35865FDC959c54dCeF3A4AbBa9d"    # Relayer USDT Production

# Endpoint e Subgraph
AZURO_API_URL = "https://api.onchainfeed.org/api/v1/public"
AZURO_REST_API = "https://api.onchainfeed.org/api/v1/public"
AZURO_ENVIRONMENT = "PolygonUSDT" 
AZURO_SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"
AZURO_PROXY = "0x7043a1215b248a329df05b5cd4da075f70a1a5b4"

# RPC Originale (1RPC)
AZURO_RPC = "https://1rpc.io/matic" 
AZURO_CHAIN_ID = 137

# Asset da monitorare per Prezzi e Mercati (SOLO CRYPTO)
ASSETS = ["BTC", "ETH", "XRP", "SOL"]
THRESHOLDS = {
    "BTC": 0.03,
    "ETH": 0.04,
    "XRP": 0.05,
    "SOL": 0.05
}

ONLY_SHORT_INTERVALS = True # Cerca solo mercati con intervalli (es. 5-15 min)

WINDOW_SECONDS = 60    # Finestra per il calcolo del movimento
MIN_ODDS = 1.80
BET_SIZE = 1.0 # USDC.e (Soglia Minima)
LOOP_INTERVAL = 5
CHAIN_ID = 137

def validate():
    if not DRY_RUN and (not PRIVATE_KEY or not WALLET_ADDRESS):
        raise EnvironmentError("Mancano credenziali nel .env")