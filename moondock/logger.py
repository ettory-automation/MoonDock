import logging
import sys
from moondock.config import LOG_LEVEL

class _NoColor:
    CYAN = ""
    GREEN = ""
    YELLOW = ""
    RED = ""
    BRIGHT = ""
    RESET_ALL = "" 

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    USE_COLORS = True
except ImportError:
    Fore = _NoColor()
    Style = _NoColor()
    USE_COLORS = False

class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if USE_COLORS:
            COLORS = {
                "DEBUG": Fore.CYAN,
                "INFO": Fore.GREEN,
                "WARNING": Fore.YELLOW,
                "ERROR": Fore.RED,
                "CRITICAL": Fore.RED + Style.BRIGHT,
            }
            color = COLORS.get(record.levelname, "")
        else:
            color = ""

        msg = super().format(record)

        return f"{color}{msg}{Style.RESET_ALL}" if USE_COLORS else msg

def create_logger() -> logging.Logger:
    logger = logging.getLogger("MoonDock")
    logger.setLevel(LOG_LEVEL)

    # Avoid duplicate handlers when reloading modules
    if logger.hasHandlers():
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LOG_LEVEL)

    formatter = ColorFormatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger

logger = create_logger()