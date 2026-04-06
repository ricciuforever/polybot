import os
from dotenv import load_dotenv
load_dotenv()

DRY_RUN = True

PRIVATE_KEY = os.getenv("PRIVATE_KEY", "").strip()
if PRIVATE_KEY and not PRIVATE_KEY.startswith("0x"): PRIVATE_KEY = "0x" + PRIVATE_KEY
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "").strip()

# Azuro V3 (Polygon) - GEM / DGPredict Configuration
AZURO_TOKEN = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC.e (PoS)
AZURO_LP = "0x2bE78663EeE0b5B891F83084C5567d89849646e7"     # Pool GEM USDC.e
AZURO_CORE = "0xF9548Be470A4e130c90ceA8b179FCD66D2972AC7" 
AZURO_SUBGRAPH_URL = "https://thegraph.azuro.org/subgraphs/name/azuro-protocol/azuro-api-polygon-v3"

# Endpoint REST API V3
AZURO_REST_API = "https://api.onchainfeed.org/api/v1/public"
# Cambiato in 1RPC per stabilità
AZURO_RPC = "https://1rpc.io/matic" 

# Asset da monitorare per Prezzi e Mercati (SOLO CRYPTO)
ASSETS = ["BTC", "ETH", "XRP", "SOL", "DOGE"]
THRESHOLDS = {
    "BTC": 0.03,
    "ETH": 0.04,
    "XRP": 0.05,
    "SOL": 0.05,
    "DOGE": 0.06
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