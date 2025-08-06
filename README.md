# Mean Reversion Trading Bot

A Python-based trading bot that implements a simple mean reversion strategy using moving averages. The bot is designed to trade EURAUR=X and EURAUD=X currency pairs using the yfinance API.

## Features

- **Simple Mean Reversion Strategy**: Uses 20-period moving average with configurable threshold
- **Real-time Data**: Fetches data from yfinance API
- **Signal Generation**: Generates BUY/SELL/HOLD signals based on price deviation from moving average
- **Backtesting**: Comprehensive backtesting engine with performance metrics
- **Risk Management**: Position sizing, stop-loss, and take-profit functionality
- **Dashboard**: Streamlit-based dashboard for monitoring and configuration
- **API**: FastAPI-based REST API for programmatic access

## Strategy Logic

The bot implements a simple mean reversion strategy:

```python
def should_trade(df, threshold=0.01):
    ma = df['Close'].rolling(window=20).mean()
    last_price = df['Close'].iloc[-1]
    last_ma = ma.iloc[-1]

    if last_price < last_ma * (1 - threshold):
        return "BUY"
    elif last_price > last_ma * (1 + threshold):
        return "SELL"
    return "HOLD"
```

**Pseudocode:**
```
if current_price < moving_average - threshold:
    place_buy_order()
elif current_price > moving_average + threshold:
    place_sell_order()
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd trading_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

The bot is configured through `config.py` with the following key settings:

- **Symbols**: EURAUR=X, EURAUD=X
- **Lookback Window**: 20 periods (default)
- **Threshold**: 1% (0.01) deviation from moving average
- **Update Interval**: 60 seconds
- **Position Size**: 2% of portfolio per trade

## Usage

### Quick Start

Run the example script to see the strategy in action:
```bash
python example.py
```

### API Server

Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Dashboard

Start the Streamlit dashboard:
```bash
streamlit run main.py dashboard
```

The dashboard will be available at `http://localhost:8501`

### Testing

Run the test script:
```bash
python simple_test.py
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /status` - Get trading bot status
- `POST /start` - Start live trading
- `POST /stop` - Stop live trading
- `GET /strategy/params` - Get strategy parameters
- `POST /strategy/params` - Update strategy parameters
- `POST /backtest` - Run backtest simulation
- `GET /portfolio` - Get portfolio summary
- `GET /trades` - Get trade history

## Strategy Parameters

- `lookback_window`: Moving average period (default: 20)
- `threshold`: Signal threshold (default: 0.01)
- `position_size_pct`: Position size as percentage of portfolio (default: 0.02)
- `stop_loss_pct`: Stop loss percentage (default: 0.05)
- `take_profit_pct`: Take profit percentage (default: 0.10)

## Project Structure

```
trading_bot/
├── config.py              # Configuration management
├── main.py               # Main application with API and dashboard
├── data/
│   └── data_manager.py   # Data fetching and processing
├── strategies/
│   └── strategy_manager.py # Strategy implementation
├── risk/
│   └── risk_manager.py   # Risk management
├── backtesting/
│   └── backtest_engine.py # Backtesting engine
├── optimization/
│   └── parameter_optimizer.py # Parameter optimization
├── tests/
│   └── test_basic.py     # Unit tests
├── example.py            # Example usage
├── simple_test.py        # Simple test script
└── requirements.txt      # Dependencies
```

## Dependencies

- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **yfinance**: Yahoo Finance API
- **fastapi**: Web API framework
- **streamlit**: Dashboard framework
- **plotly**: Interactive charts
- **sqlalchemy**: Database ORM
- **structlog**: Structured logging

## License

This project is licensed under the MIT License.

## Disclaimer

This trading bot is for educational and research purposes only. Trading involves risk, and past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor before making investment decisions. 