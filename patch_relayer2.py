import re

file_path = '/app/modules/redeem.py'
with open(file_path, 'r') as f:
    content = f.read()

old_code = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                }"""

new_code = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                }
                if hasattr(config, 'RELAYER_API_KEY_ADDRESS') and config.RELAYER_API_KEY_ADDRESS:
                    headers["poly-relayer-api-key-address"] = config.RELAYER_API_KEY_ADDRESS"""

content = content.replace(old_code, new_code)

old_code2 = """            except Exception as e:
                log.debug(f"Errore tentativo Relayer {tx_type}: {e}")
                continue"""

new_code2 = """            except Exception as e:
                log.debug(f"Errore tentativo Relayer {tx_type}: {e}")
                continue

            # Anti-rate limit: un po' di respiro tra un tentativo e l'altro
            time.sleep(2.5)"""

content = content.replace(old_code2, new_code2)

with open(file_path, 'w') as f:
    f.write(content)
