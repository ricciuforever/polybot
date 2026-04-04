import re

file_path = '/app/modules/redeem.py'
with open(file_path, 'r') as f:
    content = f.read()

# I want to add some log to see the API headers sent (for debugging the 401 error)
# And the 429 logic is already present from patch_relayer_final.py

debug_code = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": str(config.RELAYER_API_KEY).strip(),
                }
                if hasattr(config, 'RELAYER_API_KEY_ADDRESS') and config.RELAYER_API_KEY_ADDRESS:
                    headers["poly-relayer-api-key-address"] = str(config.RELAYER_API_KEY_ADDRESS).strip()"""

debug_code_new = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": str(config.RELAYER_API_KEY).strip(),
                }
                if hasattr(config, 'RELAYER_API_KEY_ADDRESS') and config.RELAYER_API_KEY_ADDRESS:
                    headers["poly-relayer-api-key-address"] = str(config.RELAYER_API_KEY_ADDRESS).strip()

                # Non logghiamo la chiave intera, ma verifichiamo che ci sia
                key_preview = str(config.RELAYER_API_KEY).strip()[:5] + "..." if config.RELAYER_API_KEY else "None"
                # log.debug(f"Headers inviati al relayer: poly-relayer-api-key={key_preview}")"""

content = content.replace(debug_code, debug_code_new)

with open(file_path, 'w') as f:
    f.write(content)
