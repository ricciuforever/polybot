import re

file_path = '/app/modules/redeem.py'
with open(file_path, 'r') as f:
    content = f.read()

old_code = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                }"""

# Aggiungiamo anche poly-relayer-api-key-address che secondo i config sembra esistere e serve per far funzionare l'auth
# Potremmo anche aggiungere delay per l'errore 429
new_code = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                    "poly-relayer-api-key-address": config.RELAYER_API_KEY_ADDRESS,
                }"""

content = content.replace(old_code, new_code)

old_code2 = """            except Exception as e:
                log.debug(f"Errore tentativo Relayer {tx_type}: {e}")
                continue"""

new_code2 = """            except Exception as e:
                log.debug(f"Errore tentativo Relayer {tx_type}: {e}")
                continue

            # Aggiungiamo un ritardo tra i tentativi per evitare l'errore 429 (Too Many Requests)
            import time
            time.sleep(2)"""

content = content.replace(old_code2, new_code2)

with open(file_path, 'w') as f:
    f.write(content)
