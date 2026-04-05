import os
import re

config_path = "config.py"
with open(config_path, "r") as f:
    content = f.read()

# Assicuriamoci che DRY_RUN in config sia corretto e mostri che il default è True
content = re.sub(
    r'DRY_RUN\s*=\s*os\.getenv\("DRY_RUN",\s*"(.*?)"\)\.lower\(\)\s*!=\s*"false"',
    r'DRY_RUN         = os.getenv("DRY_RUN", "True").lower() != "false"',
    content
)

with open(config_path, "w") as f:
    f.write(content)

# Controllo del file .env se esiste
if os.path.exists(".env"):
    with open(".env", "r") as f:
        env_content = f.read()

    # Se DRY_RUN è falso, commentiamolo o impostiamolo a True
    if re.search(r'^DRY_RUN\s*=\s*(false|False|0)', env_content, re.MULTILINE):
        env_content = re.sub(r'^(DRY_RUN\s*=.*)$', r'# \1\nDRY_RUN=True', env_content, flags=re.MULTILINE)
        with open(".env", "w") as f:
            f.write(env_content)
