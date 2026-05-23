import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from bot.exceptions import ConfigError

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE_PATH = BASE_DIR / "trading_bot.log"

# Base URL for Binance Futures Testnet
BINANCE_TESTNET_BASE_URL = "https://demo-fapi.binance.com"

# Setup Logger
logger = logging.getLogger("BinanceFuturesBot")
logger.setLevel(logging.DEBUG)

# Prevent duplicate log messages in some environments
logger.propagate = False

# Remove any existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# File handler (detailed, logs everything from DEBUG and above)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler (clean, warnings and above by default unless verbose)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


def get_api_credentials():
    """Retrieve API key and secret key from environment variables.

    Raises:
        ConfigError: If either BINANCE_API_KEY or BINANCE_SECRET_KEY is missing.
    """
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")

    if not api_key:
        logger.error("BINANCE_API_KEY is not defined in environment or .env file.")
        raise ConfigError("Missing BINANCE_API_KEY in environment variables.")

    if not secret_key:
        logger.error("BINANCE_SECRET_KEY is not defined in environment or .env file.")
        raise ConfigError("Missing BINANCE_SECRET_KEY in environment variables.")

    return api_key, secret_key


def set_console_verbose(verbose: bool):
    """Adjust the console logging verbosity.

    If verbose is True, print DEBUG messages to stdout as well.
    """
    if verbose:
        console_handler.setLevel(logging.DEBUG)
        logger.debug("Console logging set to verbose (DEBUG level)")
    else:
        console_handler.setLevel(logging.INFO)
