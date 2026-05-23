# 🤖 Binance Futures Testnet Trading Bot

A robust, modular, and professional Python 3.x trading bot CLI designed specifically for placing orders on the **Binance Futures Testnet (USDT-M)**. Features an interactive wizard, strong input validations, detailed file logging, custom exceptions, and support for **MARKET**, **LIMIT**, and **STOP_LIMIT** orders.

---

## 🌟 Features

*   **⚡ Multiple Order Types**: Full support for `MARKET`, `LIMIT`, and `STOP_LIMIT` orders.
*   **🧙 Interactive Wizard**: Running the bot without arguments triggers a guided wizard that walks you through parameter selection with real-time validation.
*   **🛠 Modular Clean Code**: Built using strict separation of concerns:
    *   **Validation Layer**: Sanitizes and validates values before hitting any APIs.
    *   **API/Client Layer**: Direct HTTP connections with signature generation and server time synchronization.
    *   **Order Logic Layer**: Orchestrates validation and dispatching.
    *   **CLI Layer**: Formats summaries, success cards, and error grids cleanly.
*   **⏱ Server Time Offset Sync**: Automatically syncs local time with Binance's server time on launch to prevent clock-drift signature issues.
*   **🪵 Enterprise-Grade Logging**: All request URLs, response payloads, execution payloads, and errors are cleanly logged to `trading_bot.log`.
*   **🎨 Sleek Output**: Colored terminal outputs and structural grids thanks to `colorama` and `tabulate`.

---

## 📂 Project Structure

```text
Binance Futures Testnet/
│
├── bot/
│   ├── __init__.py          # Package initialization
│   ├── client.py            # Signed API requests to Binance REST endpoint
│   ├── config.py            # Environment handling and logging setup
│   ├── exceptions.py        # Domain exceptions hierarchy
│   ├── orders.py            # Orchestrator / Order processor logic
│   └── validation.py        # Input and business validations
│
├── .env                     # Configuration keys (ignored by git)
├── .env.example             # Template file for keys
├── requirements.txt         # Project dependencies
├── main.py                  # Entrypoint script
└── README.md                # Project documentation
```

---

## 🚀 Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.8 or higher** installed.

### 2. Clone / Initialize Workspace
Navigate to your workspace directory:
```bash
cd "d:\OK\Project\Binance Futures Testnet"
```

### 3. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows (Command Prompt)
venv\Scripts\activate
# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# On macOS/Linux
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Configure Environment Variables

1. Locate the `.env.example` file in the root.
2. Copy it to `.env`:
   ```bash
   copy .env.example .env
   ```
3. Open `.env` and fill in your Binance Futures Testnet API Key and Secret:
   ```env
   BINANCE_API_KEY=your_real_futures_testnet_api_key_here
   BINANCE_SECRET_KEY=your_real_futures_testnet_secret_key_here
   ```

> [!TIP]
> **Where to get Testnet Keys?**
> Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com), register/login (with Google, GitHub, etc.), and generate a new API Key/Secret Key from the "API Key" section.

---

## ⚡ How to Run the Bot

The bot has two execution modes: **Interactive Wizard** and **Direct CLI Commands**.

### Mode A: Interactive Wizard (Recommended for testing)
Simply run the bot without arguments. It will guide you step-by-step:
```bash
python main.py
```

### Mode B: Direct CLI Execution
Place orders instantly using CLI arguments:

#### 1. MARKET Order
Places a MARKET BUY order for `0.002` BTCUSDT:
```bash
python main.py BUY MARKET 0.002 --symbol BTCUSDT
```

#### 2. LIMIT Order
Places a LIMIT SELL order for `0.001` BTCUSDT at a price of `$65,000`:
```bash
python main.py SELL LIMIT 0.001 --symbol BTCUSDT --price 65000
```

#### 3. STOP_LIMIT Order (Bonus Enhancement)
Places a Stop-Limit Buy order: trigger at `$62,000`, place limit order at `$62,050`:
```bash
python main.py BUY STOP_LIMIT 0.001 --symbol BTCUSDT --price 62050 --stop-price 62000
```

#### 🚀 Flags
*   `-h` or `--help`: View CLI usage guidelines.
*   `-v` or `--verbose`: Prints detailed raw HTTP headers, requests, and Binance JSON responses directly to the console.

---

## 🪵 How Logging Works

The application writes comprehensive logs to `trading_bot.log` in the project root.

1.  **Console Logs**: Only prints general milestones, warning prompts, and clean transaction statuses.
2.  **File Logs (`trading_bot.log`)**: Log level is set to `DEBUG` and captures:
    *   Time synchronization events (offsets).
    *   API Request signatures, target URL, and query parameters.
    *   Raw API Responses from Binance (HTTP status codes and payloads).
    *   Fully-traced errors, validation issues, and connection timeouts.

Example format inside `trading_bot.log`:
```text
2026-05-18 18:05:22,812 - BinanceFuturesBot - INFO - [config.py:46] - Time synced successfully. Local-Server Offset: -42 ms
2026-05-18 18:05:23,101 - BinanceFuturesBot - DEBUG - [client.py:65] - API Request: POST https://testnet.binancefuture.com/fapi/v1/order - Params: {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '0.002', 'recvWindow': '5000', 'timestamp': 1779113123059, 'signature': '...'}
2026-05-18 18:05:23,540 - BinanceFuturesBot - DEBUG - [client.py:77] - API Response: [200] {"orderId":293810239,"symbol":"BTCUSDT","status":"NEW","clientOrderId":"x-jG68f","price":"0.0","avgPrice":"0.0","origQty":"0.002","executedQty":"0.000","type":"MARKET","side":"BUY",...}
```

---

## ⚠️ Assumptions and Limitations

*   **Testnet Only**: All calls are strictly hardcoded to the Binance Futures Testnet endpoint (`https://testnet.binancefuture.com`). It will **never** execute on live Production funds.
*   **Asset Precision & Rules**: Binance imposes Minimum Order Quantity (LOT_SIZE) and Min Price (PRICE_FILTER) on each symbol. For example, `BTCUSDT` minimum quantity is `0.001`. E.g., submitting `0.0001` or a price mismatching tick size will return a `BinanceAPIError` (code `-1111` or `-1013`). Ensure you check the testnet symbol specs if you get filter errors.
*   **One Position Mode**: This bot submits standard orders, which works seamlessly in the default "One-Way Mode" (standard long/short positioning). If your account is in Hedged Mode, it requires specifying `positionSide` in requests.

  ---

  ### 👤 Contact

Created by Om Kale

Email : ok176471@gmail.com

Special Credit: project idea inspired by @avani.artxtech

💌 Reach out for questions or collaborations!
