import socket
import requests
import requests.adapters
import urllib3.util.connection as urllib3_cn
import config

# Salva la funzione originale per non romperla se non serve il bind
_original_create_connection = urllib3_cn.create_connection

def bound_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, socket_options=None):
    if config.BIND_IP:
        # Forza l'uso del nostro source_address locale per le chiamate (ip, port=0 significa porta assegnata dal SO)
        source_address = (config.BIND_IP, 0)
    return _original_create_connection(address, timeout=timeout, source_address=source_address, socket_options=socket_options)

def apply_ip_binding():
    """
    Applica globalmente il binding all'IP specificato in BIND_IP modificando urllib3_cn.create_connection.
    Così tutte le richieste (requests e librerie che usano requests, come py_clob_client)
    saranno effettuate usando l'IP della Finlandia come sorgente.
    """
    if config.BIND_IP:
        urllib3_cn.create_connection = bound_create_connection

def get_session():
    """Restituisce una sessione requests standard. Il bind avviene a livello globale."""
    return requests.Session()
