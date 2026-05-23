from typing import Dict, Any, Optional, Tuple
from bot.client import BinanceFuturesClient
from bot.validation import validate_all_inputs
from bot.exceptions import TradingBotError
from bot.config import logger


class OrderProcessor:
    """The business logic layer coordinating input validation, parameter preparation,

    client API calls, and standardizing responses.
    """

    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    def prepare_and_validate(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Perform validation and return a clean summary dictionary of the intent.

        Args:
            symbol: Ticker symbol (e.g. BTCUSDT)
            side: BUY or SELL
            order_type: MARKET, LIMIT, STOP_LIMIT
            quantity: Trade quantity
            price: Order price
            stop_price: Stop trigger price (for stop limit orders)

        Returns:
            A dictionary containing validated parameters.
        """
        # Validate inputs via validation layer
        s_val, side_val, type_val, qty_val, price_val, stop_price_val = validate_all_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        return {
            "symbol": s_val,
            "side": side_val,
            "order_type": type_val,
            "quantity": qty_val,
            "price": price_val,
            "stop_price": stop_price_val,
        }

    def execute_order(self, validated_params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Execute the validated order on Binance Futures Testnet.

        Args:
            validated_params: A dictionary of parameters that have already been validated.

        Returns:
            A tuple of (success_status: bool, result_details: dict, message: str)
        """
        symbol = validated_params["symbol"]
        side = validated_params["side"]
        order_type = validated_params["order_type"]
        quantity = validated_params["quantity"]
        price = validated_params["price"]
        stop_price = validated_params["stop_price"]

        logger.info(f"Submitting order request: {side} {quantity} {symbol} ({order_type})")

        try:
            raw_response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )

            # Extract output variables
            order_id = raw_response.get("orderId", "N/A")
            status = raw_response.get("status", "N/A")
            executed_qty = float(raw_response.get("executedQty", 0.0))
            avg_price = float(raw_response.get("avgPrice", 0.0))
            
            # If avg price is 0 (like in LIMIT order that hasn't filled yet),
            # check if there's a limit price we can show instead
            if avg_price == 0.0 and "price" in raw_response:
                try:
                    avg_price = float(raw_response["price"])
                except (ValueError, TypeError):
                    pass

            result = {
                "orderId": order_id,
                "status": status,
                "executedQty": executed_qty,
                "avgPrice": avg_price,
                "clientOrderId": raw_response.get("clientOrderId", "N/A"),
                "origQty": float(raw_response.get("origQty", quantity)),
                "type": raw_response.get("type", order_type)
            }

            msg = f"Order #{order_id} placed successfully! Status: {status}."
            logger.info(msg)
            return True, result, msg

        except TradingBotError as e:
            err_msg = f"Order submission failed: {str(e)}"
            logger.error(err_msg)
            return False, {}, err_msg
        except Exception as e:
            err_msg = f"Unexpected execution error: {str(e)}"
            logger.error(err_msg)
            return False, {}, err_msg
