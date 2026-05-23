class TradingBotError(Exception):
    """Base exception class for the trading bot."""
    pass


class ValidationError(TradingBotError):
    """Exception raised when input validation fails."""
    pass


class ConfigError(TradingBotError):
    """Exception raised when configuration is missing or invalid."""
    pass


class BinanceAPIError(TradingBotError):
    """Exception raised when the Binance API returns an error status code."""
    def __init__(self, message: str, status_code: int = None, error_code: int = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code

    def __str__(self):
        base = super().__str__()
        parts = []
        if self.status_code is not None:
            parts.append(f"HTTP Status: {self.status_code}")
        if self.error_code is not None:
            parts.append(f"Binance Error Code: {self.error_code}")
        if parts:
            return f"{base} ({', '.join(parts)})"
        return base


class NetworkError(TradingBotError):
    """Exception raised when network connection fails."""
    pass
