#!/usr/bin/env python3
"""Entrypoint for the Binance Futures Testnet Trading Bot."""

import sys
from bot.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)
