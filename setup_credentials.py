"""
setup_credentials.py — Genera e salva le credenziali CLOB L2 di Polymarket.

Esegui UNA SOLA VOLTA con VPN Ireland attiva:
    python setup_credentials.py

Legge la HOT_WALLET_PRIVATE_KEY dal .env, si connette al CLOB API
e genera (o deriva) le credenziali L2 (api_key, secret, passphrase).
Le salva automaticamente nel .env.
"""
import os
import re
import sys
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("HOT_WALLET_PRIVATE_KEY", "")
CLOB_URL = "https://clob.polymarket.com"
CHAIN_ID = 137

if not PRIVATE_KEY or PRIVATE_KEY == "0x...":
    print("ERRORE: HOT_WALLET_PRIVATE_KEY mancante nel .env")
    sys.exit(1)

print("=" * 55)
print("  PolyBot — Setup Credenziali CLOB")
print("=" * 55)
print(f"  Host  : {CLOB_URL}")
print(f"  Chain : Polygon ({CHAIN_ID})")
print(f"  Key   : {PRIVATE_KEY[:10]}...{PRIVATE_KEY[-6:]}")
print("=" * 55)

try:
    from py_clob_client.client import ClobClient
except ImportError:
    print("ERRORE: py-clob-client non installato. Esegui: pip install py-clob-client")
    sys.exit(1)

print("\n[1/3] Inizializzo client L1 (solo private key)...")
try:
    client = ClobClient(host=CLOB_URL, chain_id=CHAIN_ID, key=PRIVATE_KEY)
    print("      Client L1 OK")
except Exception as e:
    print(f"ERRORE client L1: {e}")
    sys.exit(1)

print("\n[2/3] Creo/derivo le credenziali L2 dal server Polymarket...")
try:
    creds = client.create_api_key()
    api_key        = creds.api_key
    api_secret     = creds.api_secret
    api_passphrase = creds.api_passphrase
    print(f"      api_key        = {api_key}")
    print(f"      api_secret     = {api_secret[:8]}...")
    print(f"      api_passphrase = {api_passphrase[:8]}...")
except Exception as e:
    print(f"\nErrore creazione credenziali: {e}")
    print("\nProvo con derive_api_key (derivazione deterministica)...")
    try:
        creds = client.derive_api_key()
        api_key        = creds.api_key
        api_secret     = creds.api_secret
        api_passphrase = creds.api_passphrase
        print(f"      api_key        = {api_key}")
        print(f"      api_secret     = {api_secret[:8]}...")
        print(f"      api_passphrase = {api_passphrase[:8]}...")
    except Exception as e2:
        print(f"ERRORE anche con derive_api_key: {e2}")
        print("\nAssicurati che la VPN NordVPN (Ireland) sia attiva e riprova.")
        sys.exit(1)

print("\n[3/3] Salvo le credenziali nel .env...")
try:
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()

    def _replace(var, value, text):
        pattern = rf"^{var}=.*$"
        replacement = f"{var}={value}"
        new_text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        if var not in new_text:
            new_text += f"\n{replacement}"
        return new_text

    content = _replace("POLY_API_KEY",    api_key,        content)
    content = _replace("POLY_SECRET",     api_secret,     content)
    content = _replace("POLY_PASSPHRASE", api_passphrase, content)

    with open(".env", "w", encoding="utf-8") as f:
        f.write(content)

    print("      .env aggiornato con successo!")
except Exception as e:
    print(f"Errore scrittura .env: {e}")
    print("\nCopia manualmente queste credenziali nel .env:")
    print(f"POLY_API_KEY={api_key}")
    print(f"POLY_SECRET={api_secret}")
    print(f"POLY_PASSPHRASE={api_passphrase}")
    sys.exit(1)

print("\n" + "=" * 55)
print("  Setup completato! Ora puoi avviare il bot:")
print("  python main.py")
print("=" * 55)
