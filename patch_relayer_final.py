import re

file_path = '/app/modules/redeem.py'
with open(file_path, 'r') as f:
    content = f.read()

# Trovare la riga che definisce l'header del relayer
# Il codice ha "headers = { ... }"

headers_code_old = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                    "poly-relayer-api-key-address": config.RELAYER_API_KEY_ADDRESS,
                }"""

# Fix: Il server aspetta il Poly-Relayer-Api-Key o potrebbe aspettare anche un rate limiting
# Inoltre, dal log: `Relayer ha rifiutato SAFE/5c3359 (429): <!doctype html>`
# E `Relayer ha rifiutato SAFE/5c3359 (401): {"error":"invalid authorization"}`

# Aggiungeremo i corretti headers e sleep per il 429
headers_code_new = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": str(config.RELAYER_API_KEY).strip(),
                }
                if hasattr(config, 'RELAYER_API_KEY_ADDRESS') and config.RELAYER_API_KEY_ADDRESS:
                    headers["poly-relayer-api-key-address"] = str(config.RELAYER_API_KEY_ADDRESS).strip()"""

content = content.replace(headers_code_old, headers_code_new)

# E aggiungeremo un time.sleep extra per le richieste 429
req_code_old = """                resp = requests.post(f"{RELAYER_URL}/submit", json=body, headers=headers, timeout=20)

                if resp.status_code in (200, 201):"""

req_code_new = """                resp = requests.post(f"{RELAYER_URL}/submit", json=body, headers=headers, timeout=20)

                if resp.status_code == 429:
                    log.warning(f"Rate limit (429) dal relayer per {tx_type}. Pausa di 5 secondi...")
                    time.sleep(5)
                    # riprova 1 volta in caso di 429
                    resp = requests.post(f"{RELAYER_URL}/submit", json=body, headers=headers, timeout=20)

                if resp.status_code in (200, 201):"""

content = content.replace(req_code_old, req_code_new)

with open(file_path, 'w') as f:
    f.write(content)
