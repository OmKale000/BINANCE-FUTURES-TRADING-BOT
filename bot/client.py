import hmac
import hashlib
import time
import urllib.parse
import requests
from typing import Dict, Any, Optional
from bot.config import logger, BINANCE_TESTNET_BASE_URL
from bot.exceptions import BinanceAPIError, NetworkError


class BinanceFuturesClient:
    """A direct REST client for Binance Futures Testnet (USDT-M) with automatic

    server time synchronization and secure request signing.
    """

    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key.encode("utf-8")
        self.base_url = BINANCE_TESTNET_BASE_URL.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "X-MBX-APIKEY": self.api_key
        })
        self.time_offset = 0
        self._sync_time()

    def _sync_time(self) -> None:
        """Fetch server time from Binance Futures and compute local-to-server time offset

        to avoid timestamp errors (e.g., -1021 invalid timestamp).
        """
        url = f"{self.base_url}/fapi/v1/time"
        logger.debug(f"Syncing server time. Request: GET {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            logger.debug(f"Syncing time Response: [{response.status_code}] {response.text.strip()}")
            
            if response.status_code == 200:
                server_time = response.json()["serverTime"]
                local_time = int(time.time() * 1000)
                self.time_offset = server_time - local_time
                logger.info(f"Time synced successfully. Local-Server Offset: {self.time_offset} ms")
            else:
                logger.warning(
                    f"Failed to sync time (HTTP {response.status_code}). "
                    "Proceeding with standard local time."
                )
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error while syncing server time: {e}. Using local time.")

    def _get_timestamp(self) -> int:
        """Get current timestamp adjusted by the computed time offset."""
        return int(time.time() * 1000) + self.time_offset

    def _sign_payload(self, query_string: str) -> str:
        """Create HMAC-SHA256 signature from the query string using the secret key."""
        return hmac.new(
            self.secret_key,
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, path: str, params: Dict[str, Any], signed: bool = False) -> Dict[str, Any]:
        """Internal helper to dispatch signed/unsigned REST API requests."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        # Prepare parameters
        request_params = params.copy()
        if signed:
            request_params["timestamp"] = self._get_timestamp()
            # Construct raw query string for signature creation using standard urlencode
            query_string = urllib.parse.urlencode(request_params)
            signature = self._sign_payload(query_string)
            request_params["signature"] = signature

        # Log request details (omitting sensitive keys since we are testnet and console might log, 
        # but secret is already safe, we log the parameters sent)
        logger.debug(f"API Request: {method} {url} - Params: {request_params}")
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=request_params, timeout=15)
            elif method.upper() == "POST":
                response = self.session.post(url, data=request_params, timeout=15)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=request_params, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log response details
            logger.debug(f"API Response: [{response.status_code}] {response.text.strip()}")

            if response.status_code == 200:
                return response.json()
            else:
                # Handle Binance Error response
                try:
                    err_json = response.json()
                    err_msg = err_json.get("msg", "Unknown error")
                    err_code = err_json.get("code", None)
                except ValueError:
                    err_msg = response.text
                    err_code = None
                
                logger.error(f"Binance API returned error status: {response.status_code}. Message: {err_msg}, Code: {err_code}")
                raise BinanceAPIError(
                    message=err_msg,
                    status_code=response.status_code,
                    error_code=err_code
                )

        except requests.exceptions.Timeout as e:
            logger.error(f"Network timeout: {e}")
            raise NetworkError("The request to Binance Futures timed out. Please try again.")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Network connection failed: {e}")
            raise NetworkError("Could not connect to Binance Futures. Check your internet connection.")
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            raise NetworkError(f"HTTP communication error: {e}")

    def ping(self) -> bool:
        """Ping the testnet servers to verify connection."""
        try:
            self._request("GET", "fapi/v1/ping", {})
            return True
        except TradingBotError:
            return False

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        recv_window: int = 5000
    ) -> Dict[str, Any]:
        """Submit a new order to Binance Futures Testnet.

        Args:
            symbol: Ticker symbol (e.g. BTCUSDT)
            side: BUY or SELL
            order_type: LIMIT, MARKET, or STOP_LIMIT
            quantity: Order quantity (base asset)
            price: Required for LIMIT and STOP_LIMIT orders
            stop_price: Required for STOP_LIMIT orders
            recv_window: Recv window parameter in milliseconds

        Returns:
            JSON response from Binance containing order receipt.
        """
        # Convert values to string parameters appropriate for Binance API
        # Explicit formatting with 8 decimals eliminates scientific notation issues for tiny/large values.
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": f"{quantity:.8f}".rstrip('0').rstrip('.'),
            "recvWindow": str(recv_window)
        }

        # Handle specific order type specifications
        if order_type in ("LIMIT", "STOP_LIMIT"):
            params["price"] = f"{price:.8f}".rstrip('0').rstrip('.')
            params["timeInForce"] = "GTC"  # Good 'Til Cancelled is standard

        if order_type == "STOP_LIMIT":
            # For Stop-Limit orders, we need both stopPrice and standard price
            params["stopPrice"] = f"{stop_price:.8f}".rstrip('0').rstrip('.')
            # For Stop-Limit, Binance Futures endpoint requires type='STOP' or 'STOP_MARKET' or 'TAKE_PROFIT' etc.
            # Usually, standard STOP-LIMIT is placed using type="STOP" with both stopPrice and price.
            # Let's map STOP_LIMIT to Binance type="STOP".
            params["type"] = "STOP"

        return self._request("POST", "fapi/v1/order", params, signed=True)
