import time
import requests
from web3 import Web3
from modules.logger import get_logger

log = get_logger("rpc_manager")

class RPCManager:
    def __init__(self, rpc_list=None):
        self.rpc_list = rpc_list or [
            "https://polygon-public.nodies.app",
            "https://polygon-bor-rpc.publicnode.com",
            "https://polygon.llamarpc.com",
            "https://rpc-mainnet.matic.quiknode.pro",
            "https://1rpc.io/matic"
        ]
        self.current_index = 0
        self.w3 = self._connect()

    def _connect(self):
        url = self.rpc_list[self.current_index]
        log.info(f"🔌 Tentativo connessione RPC: {url}")
        return Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))

    def next_rpc(self):
        self.current_index = (self.current_index + 1) % len(self.rpc_list)
        self.w3 = self._connect()
        log.warning(f"🔄 Passaggio al prossimo RPC: {self.rpc_list[self.current_index]}")

    def get_w3(self):
        return self.w3

    def call_safe(self, func, *args, **kwargs):
        """Esegue una chiamata Web3 con fallback automatico."""
        for attempt in range(len(self.rpc_list)):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "unauthorized" in err_str or "401" in err_str or "timeout" in err_str:
                    log.error(f"❌ Errore RPC ({self.rpc_list[self.current_index]}): {e}")
                    self.next_rpc()
                else:
                    raise e
        raise Exception("🚫 Tutti i nodi RPC hanno fallito.")

if __name__ == "__main__":
    manager = RPCManager()
    # Test safe call
    block = manager.call_safe(manager.w3.eth.get_block_number)
    print(f"Current Block: {block}")
