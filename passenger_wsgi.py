import sys
import os

# Aggiunge la root folder al path per assicurarsi che i moduli vengano visti
sys.path.insert(0, os.path.dirname(__file__))

# Phusion Passenger cerca la variabile "application" per avviare il web server
from web_server_v2 import app as application
