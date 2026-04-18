"""
modules/price_feed.py — WebSocket Binance Multi-Asset in tempo reale.
"""
import json
import time
import threading
from collections import deque
import websocket
import config
from modules.logger import get_logger

log = get_logger("price_feed")

class BinanceFeed:
    def __init__(self):
        self._lock   = threading.Lock()
        self._windows = {asset: deque() for asset in config.ASSETS}
        self._last_prices = {asset: 0.0 for asset in config.ASSETS}
        self._ws = None
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._run, daemon=True, name="binance-feed")
        t.start()
        log.info(f"BinanceFeed avviato (WebSocket Multi-Asset: {', '.join(config.ASSETS)})")

    def stop(self):
        self._running = False
        if self._ws:
            self._ws.close()

    def get_last_price(self, asset: str) -> float:
        with self._lock:
            return self._last_prices.get(asset, 0.0)

    def get_window_movement(self, asset: str) -> float:
        now = time.time()
        cutoff_window = now - config.WINDOW_SECONDS
        cutoff_trend = now - 600  # 10 minuti di buffer storico

        with self._lock:
            window = self._windows.get(asset)
            if not window: return 0.0

            # Rimuovi punti più vecchi di 10 minuti
            while window and window[0][0] < cutoff_trend:
                window.popleft()

            if len(window) < 2:
                return 0.0

            # Trova il prezzo all'inizio della finestra (WINDOW_SECONDS)
            oldest_price_in_window = window[-1][1]
            for ts, p in reversed(window):
                if ts < cutoff_window:
                    break
                oldest_price_in_window = p

            newest_price = window[-1][1]

        if oldest_price_in_window == 0:
            return 0.0

        return ((newest_price - oldest_price_in_window) / oldest_price_in_window) * 100

    def get_price_at_time(self, asset: str, target_ts: float) -> float:
        """Recupera il prezzo più vicino a un timestamp passato dal buffer storico."""
        with self._lock:
            window = self._windows.get(asset)
            if not window:
                return 0.0
            
            # Cerca il prezzo più vicino al timestamp target
            best_price = 0.0
            best_diff = float('inf')
            for ts, price in window:
                diff = abs(ts - target_ts)
                if diff < best_diff:
                    best_diff = diff
                    best_price = price
            
            return best_price

    def get_trend_direction(self, asset: str) -> int:
        """Ritorna 1 se il trend a 5m è UP, -1 se DOWN, 0 se neutrale."""
        with self._lock:
            window = self._windows.get(asset)
            if not window or len(window) < 10:
                return 0
            prices = [p for ts, p in window]
            sma = sum(prices) / len(prices)
            last = self._last_prices.get(asset, 0.0)
            if last > sma:
                return 1
            elif last < sma:
                return -1
            return 0

    def _on_message(self, ws, message):
        try:
            raw = json.loads(message)
            stream = raw.get("stream", "")
            data = raw.get("data", {})
            
            if not stream or not data:
                return

            # Estrai l'asset dal nome dello stream (es. "btcusdt@aggTrade" -> "BTC")
            asset = stream.split("usdt")[0].upper()
            if asset not in config.ASSETS:
                return

            price = float(data["p"])
            ts = time.time()

            with self._lock:
                self._last_prices[asset] = price
                self._windows[asset].append((ts, price))
        except Exception:
            log.exception("Errore parsing messaggio Binance:")

    def _on_error(self, ws, error):
        log.error(f"WebSocket Binance errore: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        log.warning(f"WebSocket Binance chiuso ({close_status_code}). Riconnessione...")
        if self._running:
            time.sleep(3)
            self._run()

    def _on_open(self, ws):
        log.info("WebSocket Binance Multi-Asset connesso.")

    def _run(self):
        # Crea l'URL combinato per tutti gli asset supportati
        streams = "/".join([f"{asset.lower()}usdt@aggTrade" for asset in config.ASSETS])
        wss_url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        
        self._ws = websocket.WebSocketApp(
            wss_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )
        self._ws.run_forever()
