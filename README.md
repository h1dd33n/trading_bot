# Advanced Mean Reversion Trading Bot

A comprehensive, production-ready trading bot implementing advanced mean reversion strategies with real-time data processing, risk management, and parameter optimization.

## 🚀 Features

### Core Features
- **Multiple Mean Reversion Strategies**: Z-score, Bollinger Bands, and RSI-based mean reversion
- **Real-time Data Processing**: Live market data with caching and optimization
- **Comprehensive Risk Management**: Position sizing, stop-loss, take-profit, and portfolio constraints
- **Advanced Backtesting Engine**: Step-by-step simulation with detailed performance metrics
- **Parameter Optimization**: Easy tweaking of all strategy parameters for better results
- **Live Trading Support**: Paper trading and live trading modes
- **Interactive Dashboard**: Real-time monitoring and control via Streamlit

### Enhanced Features
- **Dynamic Risk Adjustment**: Kelly criterion and performance-based position sizing
- **Multi-Asset Support**: Trade multiple symbols simultaneously
- **Database Storage**: PostgreSQL with TimescaleDB for historical data
- **API Integration**: FastAPI REST API for external control
- **Comprehensive Logging**: Structured logging with performance monitoring
- **Modular Architecture**: Clean, maintainable code structure

## 📊 Strategy Types

### 1. Mean Reversion (Z-Score)
- Uses statistical z-score to identify overbought/oversold conditions
- Configurable lookback window and threshold parameters
- Signal confirmation over multiple periods

### 2. Bollinger Bands
- Standard deviation-based mean reversion
- Upper/lower band breakouts for entry signals
- Dynamic band width for confidence calculation

### 3. RSI Mean Reversion
- RSI-based oversold/overbought detection
- Configurable RSI periods and thresholds
- Combines momentum and mean reversion concepts

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- PostgreSQL (optional, for data storage)
- Git

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd trading_bot
```

2. **Create virtual environment**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install core dependencies**
```bash
pip install -r requirements.txt
```

4. **(Optional) Install Interactive Brokers API**
   - **Method 1**: Download from [Interactive Brokers API page](https://www.interactivebrokers.com/en/trading/ib-api.html)
     ```bash
     pip install /path/to/downloaded/ibapi
     ```
   - **Method 2**: Use community-maintained version
     ```bash
     pip install git+https://github.com/erdewit/ib_insync.git
     ```

5. **(Optional) Install additional dependencies**
```bash
pip install -r requirements-optional.txt
```

4. **Environment configuration**
Create a `.env` file in the root directory:
```env
# Database Configuration
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__DATABASE=trading_bot
DATABASE__USERNAME=postgres
DATABASE__PASSWORD=your_password

# Trading Configuration
STRATEGY__STRATEGY_TYPE=mean_reversion
STRATEGY__LOOKBACK_WINDOW=20
STRATEGY__Z_SCORE_THRESHOLD=2.0
STRATEGY__POSITION_SIZE_PCT=0.02
STRATEGY__STOP_LOSS_PCT=0.05
STRATEGY__TAKE_PROFIT_PCT=0.10

# Data Configuration
DATA__SYMBOLS=["AAPL", "MSFT", "GOOGL"]
DATA__TIMEFRAMES=["1h", "4h", "1d"]
DATA__UPDATE_INTERVAL=60

# Risk Management
RISK__MAX_PORTFOLIO_RISK=0.02
RISK__MAX_DRAWDOWN_PCT=0.20
RISK__KELLY_CRITERION=true
```

## 🚀 Quick Start

### 1. Run Backtest
```python
import asyncio
from datetime import datetime
from backtesting.backtest_engine import get_backtest_engine

async def run_quick_backtest():
    engine = await get_backtest_engine()
    
    results = await engine.run_backtest(
        symbols=["AAPL", "MSFT"],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=100000.0
    )
    
    engine.print_summary()

asyncio.run(run_quick_backtest())
```

### 2. Start API Server
```bash
python main.py
```
Access the API at `http://localhost:8000`

### 3. Launch Dashboard
```bash
streamlit run main.py
```
Access the dashboard at `http://localhost:8501`

## 📈 Parameter Optimization

All strategy parameters are easily tweakable for better results:

### Key Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `lookback_window` | Period for mean calculation | 20 | 5-50 |
| `z_score_threshold` | Z-score threshold for signals | 2.0 | 1.0-3.0 |
| `position_size_pct` | Position size as % of portfolio | 0.02 | 0.01-0.10 |
| `stop_loss_pct` | Stop loss percentage | 0.05 | 0.01-0.20 |
| `take_profit_pct` | Take profit percentage | 0.10 | 0.05-0.30 |
| `rsi_period` | RSI calculation period | 14 | 10-20 |
| `rsi_oversold` | RSI oversold threshold | 30 | 20-40 |
| `rsi_overbought` | RSI overbought threshold | 70 | 60-80 |

### Dynamic Updates
```python
from config import update_strategy_params

# Update parameters dynamically
update_strategy_params({
    'z_score_threshold': 2.5,
    'position_size_pct': 0.03,
    'stop_loss_pct': 0.03
})
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - API information
- `GET /status` - Trading bot status
- `POST /start` - Start live trading
- `POST /stop` - Stop live trading

### Strategy Management
- `GET /strategy/params` - Get current parameters
- `POST /strategy/params` - Update parameters

### Backtesting
- `POST /backtest` - Run backtest simulation

### Portfolio
- `GET /portfolio` - Portfolio summary
- `GET /trades` - Trade history

## 📊 Performance Metrics

The bot tracks comprehensive performance metrics:

- **Total Return**: Absolute and percentage returns
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Trade Statistics**: Average win/loss, best/worst trades

## 🏗️ Architecture

```
trading_bot/
├── config.py              # Configuration management
├── data/
│   └── data_manager.py    # Data fetching and storage
├── strategies/
│   └── strategy_manager.py # Strategy implementation
├── risk/
│   └── risk_manager.py    # Risk management
├── backtesting/
│   └── backtest_engine.py # Backtesting engine
├── main.py               # Main application
├── requirements.txt      # Dependencies
└── README.md           # This file
```

## 🔒 Risk Management

### Position Sizing
- Kelly criterion for optimal position sizing
- Dynamic risk adjustment based on performance
- Portfolio-level constraints

### Risk Limits
- Maximum drawdown protection
- Correlation-based diversification
- Sector exposure limits
- Leverage constraints

### Stop Loss & Take Profit
- Automatic stop-loss and take-profit orders
- Trailing stops (configurable)
- Time-based exits

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

## 📝 Configuration

### Environment Variables
All parameters can be configured via environment variables:

```bash
# Strategy parameters
export STRATEGY__Z_SCORE_THRESHOLD=2.5
export STRATEGY__POSITION_SIZE_PCT=0.03

# Data configuration
export DATA__SYMBOLS='["AAPL", "MSFT", "GOOGL"]'

# Risk management
export RISK__MAX_DRAWDOWN_PCT=0.15
```

### Configuration File
Create a `config.yaml` file for complex configurations:

```yaml
strategy:
  strategy_type: mean_reversion
  lookback_window: 20
  z_score_threshold: 2.0
  position_size_pct: 0.02

risk:
  max_drawdown_pct: 0.20
  kelly_criterion: true
  max_leverage: 1.0
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Production Considerations
- Use PostgreSQL for data persistence
- Implement proper logging and monitoring
- Set up alerts for critical events
- Use environment variables for secrets
- Implement proper error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This trading bot is for educational and research purposes. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always test thoroughly before using with real money.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the example configurations

---

**Happy Trading! 📈** 