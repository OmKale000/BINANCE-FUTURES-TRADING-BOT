import re
from typing import Optional, Tuple
from bot.exceptions import ValidationError

# RegEx for basic symbols (e.g. BTCUSDT, ETHUSDT)
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9-]{3,15}$")


def validate_symbol(symbol: str) -> str:
    """Validate that the ticker symbol is structurally sound.

    Args:
        symbol: The asset symbol (e.g. BTCUSDT)

    Returns:
        The validated symbol in uppercase.

    Raises:
        ValidationError: If the symbol doesn't match standard patterns.
    """
    if not symbol:
        raise ValidationError("Symbol must not be empty.")
    
    clean_symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(clean_symbol):
        raise ValidationError(
            f"Invalid symbol format: '{symbol}'. "
            "Symbol must be alphanumeric and between 3 to 15 characters long (e.g., BTCUSDT)."
        )
    return clean_symbol


def validate_side(side: str) -> str:
    """Validate the order side.

    Args:
        side: The order side (e.g., BUY, SELL)

    Returns:
        Validated side in uppercase ("BUY" or "SELL").

    Raises:
        ValidationError: If the side is not BUY or SELL.
    """
    if not side:
        raise ValidationError("Order side must not be empty.")
    
    clean_side = side.strip().upper()
    if clean_side not in ("BUY", "SELL"):
        raise ValidationError(f"Invalid order side: '{side}'. Side must be BUY or SELL.")
    return clean_side


def validate_order_type(order_type: str) -> str:
    """Validate the order type. Supports LIMIT, MARKET, and STOP_LIMIT.

    Args:
        order_type: The type of the order.

    Returns:
        Validated order type in uppercase.

    Raises:
        ValidationError: If type is unsupported.
    """
    if not order_type:
        raise ValidationError("Order type must not be empty.")
    
    clean_type = order_type.strip().upper()
    allowed_types = ("MARKET", "LIMIT", "STOP_LIMIT")
    if clean_type not in allowed_types:
        raise ValidationError(
            f"Invalid order type: '{order_type}'. "
            f"Allowed types: {', '.join(allowed_types)}."
        )
    return clean_type


def validate_quantity(quantity: float) -> float:
    """Validate that the quantity is a positive float.

    Args:
        quantity: The size of the order.

    Returns:
        Validated quantity as a float.

    Raises:
        ValidationError: If quantity is <= 0 or not a valid number.
    """
    try:
        qty_float = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity must be a numeric value, got '{quantity}'.")

    if qty_float <= 0:
        raise ValidationError(f"Quantity must be strictly positive, got {qty_float}.")
    return qty_float


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """Validate the price according to the order type.

    - LIMIT & STOP_LIMIT order: Price is required and must be a positive float.
    - MARKET order: Price must be omitted (None or empty).

    Args:
        price: Price for the order.
        order_type: Validated order type (MARKET, LIMIT, STOP_LIMIT).

    Returns:
        Validated price or None.

    Raises:
        ValidationError: If price rules are violated.
    """
    if order_type in ("LIMIT", "STOP_LIMIT"):
        if price is None:
            raise ValidationError(f"Price is required for '{order_type}' orders.")
        try:
            price_float = float(price)
        except (ValueError, TypeError):
            raise ValidationError(f"Price must be a numeric value, got '{price}'.")
        
        if price_float <= 0:
            raise ValidationError(f"Price must be strictly positive, got {price_float}.")
        return price_float
    else:
        # MARKET order
        if price is not None:
            raise ValidationError("Price must not be provided for MARKET orders.")
        return None


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    """Validate the stop_price according to the order type.

    - STOP_LIMIT order: Stop price is required and must be a positive float.
    - Others: Must be omitted.

    Args:
        stop_price: Stop price for the order.
        order_type: Validated order type.

    Returns:
        Validated stop price or None.

    Raises:
        ValidationError: If rules are violated.
    """
    if order_type == "STOP_LIMIT":
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        try:
            stop_float = float(stop_price)
        except (ValueError, TypeError):
            raise ValidationError(f"Stop price must be a numeric value, got '{stop_price}'.")
        
        if stop_float <= 0:
            raise ValidationError(f"Stop price must be strictly positive, got {stop_float}.")
        return stop_float
    else:
        if stop_price is not None:
            raise ValidationError("Stop price must not be provided for non-STOP_LIMIT orders.")
        return None


def validate_all_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Tuple[str, str, str, float, Optional[float], Optional[float]]:
    """Validate all order parameters.

    Returns:
        Tuple of (symbol, side, order_type, quantity, price, stop_price) normalized.

    Raises:
        ValidationError: If any field fails validation.
    """
    s_val = validate_symbol(symbol)
    side_val = validate_side(side)
    type_val = validate_order_type(order_type)
    qty_val = validate_quantity(quantity)
    price_val = validate_price(price, type_val)
    stop_price_val = validate_stop_price(stop_price, type_val)

    return s_val, side_val, type_val, qty_val, price_val, stop_price_val
