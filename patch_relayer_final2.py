import re

file_path = '/app/modules/redeem.py'
with open(file_path, 'r') as f:
    content = f.read()

# Il file era già stato modificato ma non committato
old_headers = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                    "poly-relayer-api-key-address": config.RELAYER_API_KEY_ADDRESS,
                }"""

new_headers = """                # Crucial Fix: Standard Headers matching the polymarket webapp
                headers = {
                    "Content-Type": "application/json",
                    "poly-relayer-api-key": config.RELAYER_API_KEY,
                    "poly-relayer-api-key-address": config.RELAYER_API_KEY_ADDRESS,
                }"""

# Since I ran python patch_relayer.py, it got replaced already. Let's see what is inside currently.
