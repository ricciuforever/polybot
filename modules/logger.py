import logging
import os
from logging.handlers import RotatingFileHandler
from collections import deque
from colorama import init, Fore, Style

# Buffer circolare per i log in memoria (per la dashboard web)
LOG_BUFFER = deque(maxlen=20)

init(autoreset=True)

# Assicuriamoci che la cartella logs esista
os.makedirs("logs", exist_ok=True)

# Formattazione per i file di log
_file_fmt = logging.Formatter(
    fmt="%(asctime)s [%(levelname)8s] %(name)s [%(filename)s:%(lineno)d] — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class _ColorFormatter(logging.Formatter):
    """Formatter colorato per la console."""
    COLORS = {
        logging.DEBUG:    Fore.CYAN,
        logging.INFO:     Fore.GREEN,
        logging.WARNING:  Fore.YELLOW,
        logging.ERROR:    Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        orig_levelname = record.levelname
        record.levelname = f"{color}{orig_levelname:8}{Style.RESET_ALL}"
        
        # Non coloriamo il messaggio se è destinato al buffer memoria (sarà fatto nel dashboard)
        orig_msg = record.msg
        record.msg = f"{color}{orig_msg}{Style.RESET_ALL}"
        res = super().format(record)
        
        # Ripristiniamo per non sporcare altri handler
        record.levelname = orig_levelname
        record.msg = orig_msg
        return res

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)

    # 1. Console Handler (COLORATO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(_ColorFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(ch)

    # 2. General Log (ROTATING - max 5MB, keeps 3 backups)
    fh = RotatingFileHandler("logs/bot.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(_file_fmt)
    logger.addHandler(fh)

    # 3. Error Log (ROTATING - solo ERROR e superiori)
    eh = RotatingFileHandler("logs/error.log", maxBytes=2*1024*1024, backupCount=5, encoding="utf-8")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(_file_fmt)
    logger.addHandler(eh)

    # 4. Memory Handler (per Dashboard Web)
    class MemoryHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            LOG_BUFFER.append(msg)
    
    mh = MemoryHandler()
    mh.setFormatter(logging.Formatter(fmt='%(asctime)s [%(levelname)-5s] %(name)s — %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(mh)

    return logger
