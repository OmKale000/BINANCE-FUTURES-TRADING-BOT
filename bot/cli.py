import sys
from typing import Optional
import click
from colorama import init, Fore, Style
from tabulate import tabulate

from bot.config import get_api_credentials, logger, set_console_verbose
from bot.client import BinanceFuturesClient
from bot.orders import OrderProcessor
from bot.exceptions import ConfigError, ValidationError, TradingBotError

# Initialize colorama for cross-platform color support
init(autoreset=True)


def print_header(title: str):
    """Print a styled section header."""
    click.echo(Fore.CYAN + Style.BRIGHT + "=" * 50)
    click.echo(Fore.CYAN + Style.BRIGHT + f" {title.upper()} ")
    click.echo(Fore.CYAN + Style.BRIGHT + "=" * 50)


def print_success_card(message: str, details: dict):
    """Print order placement success details in a beautiful tabular card format."""
    click.echo("\n" + Fore.GREEN + Style.BRIGHT + "[SUCCESS] " + message)
    
    # Structure details for tabulate
    table_data = [[Fore.YELLOW + k, Fore.WHITE + str(v)] for k, v in details.items()]
    click.echo(tabulate(table_data, headers=[Fore.CYAN + "Parameter", Fore.CYAN + "Value"], tablefmt="grid"))
    click.echo(Fore.GREEN + "=" * 50 + "\n")


def print_failure_card(message: str):
    """Print failure card in bright red."""
    click.echo("\n" + Fore.RED + Style.BRIGHT + "[EXECUTION FAILURE]")
    click.echo(Fore.RED + "-" * 50)
    click.echo(Fore.RED + f"Reason: {message}")
    click.echo(Fore.RED + "=" * 50 + "\n")


def run_interactive_wizard() -> tuple:
    """Prompt the user step-by-step with real-time validation to form an order."""
    print_header("Binance Futures Order Wizard")
    
    # 1. Symbol
    symbol = click.prompt(
        Fore.WHITE + "Enter Symbol (e.g., BTCUSDT, ETHUSDT)",
        type=str,
        default="BTCUSDT"
    ).strip().upper()
    
    # 2. Side
    side = click.prompt(
        Fore.WHITE + "Select Order Side",
        type=click.Choice(["BUY", "SELL"], case_sensitive=False),
        default="BUY"
    ).upper()
    
    # 3. Order Type
    order_type = click.prompt(
        Fore.WHITE + "Select Order Type",
        type=click.Choice(["MARKET", "LIMIT", "STOP_LIMIT"], case_sensitive=False),
        default="MARKET"
    ).upper()
    
    # 4. Quantity
    quantity = click.prompt(
        Fore.WHITE + "Enter Quantity (e.g., 0.001)",
        type=float
    )
    
    # 5. Price (only if LIMIT or STOP_LIMIT)
    price = None
    if order_type in ("LIMIT", "STOP_LIMIT"):
        price = click.prompt(
            Fore.WHITE + f"Enter Limit Price for {order_type}",
            type=float
        )
        
    # 6. Stop Price (only if STOP_LIMIT)
    stop_price = None
    if order_type == "STOP_LIMIT":
        stop_price = click.prompt(
            Fore.WHITE + "Enter Stop Trigger Price",
            type=float
        )
        
    return symbol, side, order_type, quantity, price, stop_price


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("side", required=False, type=click.Choice(["BUY", "SELL"], case_sensitive=False))
@click.argument("order_type", required=False, type=click.Choice(["MARKET", "LIMIT", "STOP_LIMIT"], case_sensitive=False))
@click.argument("quantity", required=False, type=float)
@click.option("-s", "--symbol", type=str, default="BTCUSDT", help="Asset ticker symbol, e.g. BTCUSDT")
@click.option("-p", "--price", type=float, help="Limit price (Required for LIMIT/STOP_LIMIT, omit for MARKET)")
@click.option("-t", "--stop-price", type=float, help="Stop trigger price (Required for STOP_LIMIT)")
@click.option("-i", "--interactive", is_flag=True, help="Force interactive execution wizard")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose output (detailed HTTP request/responses)")
def main(
    side: Optional[str],
    order_type: Optional[str],
    quantity: Optional[float],
    symbol: str,
    price: Optional[float],
    stop_price: Optional[float],
    interactive: bool,
    verbose: bool
):
    """Binance Futures Testnet Trading Bot CLI

    Place BUY or SELL orders (MARKET, LIMIT, STOP_LIMIT) instantly and securely on the Futures Testnet.
    
    If no positional arguments are passed, it automatically enters interactive wizard mode.
    """
    # Configure verbosity
    set_console_verbose(verbose)
    
    print_header("Binance Futures Trading Bot")
    
    # Verify Credentials early
    try:
        api_key, secret_key = get_api_credentials()
    except ConfigError as ce:
        click.echo(Fore.RED + f"\nConfiguration Error: {ce}")
        click.echo(Fore.YELLOW + "\nTo fix this:")
        click.echo(Fore.WHITE + "  1. Copy '.env.example' to '.env'")
        click.echo(Fore.WHITE + "  2. Populate 'BINANCE_API_KEY' and 'BINANCE_SECRET_KEY' inside '.env'")
        click.echo(Fore.WHITE + "  3. Re-run this script.")
        sys.exit(1)

    # Determine if we should trigger interactive wizard
    # We do so if -i is supplied OR if side/order_type/quantity are missing.
    is_interactive = interactive or (side is None and order_type is None and quantity is None)
    
    if is_interactive:
        try:
            symbol, side, order_type, quantity, price, stop_price = run_interactive_wizard()
        except click.Abort:
            click.echo(Fore.YELLOW + "\nWizard aborted by user.")
            sys.exit(0)

    # Initialize Binance client and process order
    try:
        # 1. Initialize Client
        client = BinanceFuturesClient(api_key, secret_key)
        processor = OrderProcessor(client)
        
        # 2. Validate inputs in business layer
        logger.debug("Validating parameters...")
        validated = processor.prepare_and_validate(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )

        # 3. Print Order Request Summary
        click.echo("\n" + Fore.YELLOW + Style.BRIGHT + "[ORDER REQUEST SUMMARY]")
        click.echo(Fore.YELLOW + "-" * 50)
        
        summary_table = [
            ["Symbol", validated["symbol"]],
            ["Side", validated["side"]],
            ["Order Type", validated["order_type"]],
            ["Quantity", validated["quantity"]],
        ]
        if validated["price"] is not None:
            summary_table.append(["Price", f"{validated['price']:.4f}"])
        if validated["stop_price"] is not None:
            summary_table.append(["Stop Price", f"{validated['stop_price']:.4f}"])
            
        click.echo(tabulate(summary_table, headers=["Parameter", "Specification"], tablefmt="simple"))
        click.echo(Fore.YELLOW + "-" * 50)

        # 4. Confirm submission
        if click.confirm(Fore.GREEN + "Do you want to submit this order to Binance Futures Testnet?", default=True):
            # Place Order
            click.echo(Fore.CYAN + "Submitting order to testnet...")
            success, details, msg = processor.execute_order(validated)
            
            if success:
                print_success_card(msg, details)
            else:
                print_failure_card(msg)
        else:
            click.echo(Fore.YELLOW + "Order submission cancelled by user.")

    except click.Abort:
        click.echo(Fore.YELLOW + "\nOperation cancelled or aborted by user. Exiting...")
        sys.exit(0)
    except ValidationError as ve:
        logger.error(f"Input validation failed: {ve}")
        print_failure_card(f"Input validation error: {ve}")
    except TradingBotError as tbe:
        logger.error(f"Execution failed: {tbe}")
        print_failure_card(str(tbe))
    except Exception as e:
        logger.error(f"An unexpected critical error occurred: {e}", exc_info=True)
        print_failure_card(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
