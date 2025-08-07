# MT5 Trading Bots

This module contains MT5 trading bots for both regular and prop firm accounts with different risk management strategies.

## Features

### Regular Trading Bot
- Uses pip sizes for position sizing instead of account size
- Standard risk management (5% daily loss, 10% overall loss)
- Mean reversion strategy with RSI and SMA indicators
- Supports multiple currency pairs

### Prop Firm Trading Bot
- Strict risk management (2% daily loss, 4% overall loss)
- Conservative position sizing (1% per trade)
- Tighter stop losses and take profits
- YFinance backtesting for strategy validation
- Maximum 3 concurrent positions

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install MetaTrader5 terminal and ensure it's running

3. Configure your MT5 account credentials in `mt5_config.py`

## Configuration

### Account Settings
The bots are configured with the following MT5 account settings:
- Server: ACGMarkets-Main
- Login: 2194718
- Password: vUD&V86dwc

### Risk Management

#### Regular Account
- Max daily loss: 5% of account balance
- Max overall loss: 10% of account balance
- Position size: 2% of account balance per trade
- Max positions: 10 concurrent trades

#### Prop Firm Account
- Max daily loss: 2% of account balance
- Max overall loss: 4% of account balance
- Position size: 1% of account balance per trade
- Max positions: 3 concurrent trades
- Minimum signal strength: 70%

## Usage

### Running Individual Bots

#### Regular Trading Bot
```python
from mt5.mt5_trading_bot import MT5TradingBot
from mt5.mt5_config import AccountType

bot = MT5TradingBot(AccountType.REGULAR)
await bot.initialize()
await bot.start_trading()
```

#### Prop Firm Trading Bot
```python
from mt5.mt5_prop_firm_bot import MT5PropFirmBot

bot = MT5PropFirmBot()
await bot.initialize()
await bot.start_trading()
```

### Running Both Bots with Launcher

```bash
# Run both bots
python mt5/run_mt5_bots.py

# Run only regular bot
python mt5/run_mt5_bots.py --regular

# Run only prop firm bot
python mt5/run_mt5_bots.py --prop-firm

# Run with monitoring
python mt5/run_mt5_bots.py --monitor

# Run for specific duration (2 hours)
python mt5/run_mt5_bots.py --duration 7200

# Run backtest only
python mt5/run_mt5_bots.py --backtest
```

### Backtesting

The prop firm bot includes YFinance backtesting capabilities:

```python
from mt5.mt5_prop_firm_bot import YFinanceBacktester

backtester = YFinanceBacktester(
    symbols=["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"],
    initial_capital=100000
)

result = backtester.run_backtest(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## Trading Strategy

### Signal Generation
Both bots use a mean reversion strategy based on:
- RSI (Relative Strength Index) - 14 period
- SMA (Simple Moving Average) - 20 and 50 period
- ATR (Average True Range) - for position sizing

### Entry Conditions
- **Buy Signal**: RSI < 30 (or 25 for prop firm) and price below SMA
- **Sell Signal**: RSI > 70 (or 75 for prop firm) and price above SMA

### Exit Conditions
- Stop Loss: 20 pips (regular) or 1.5 ATR (prop firm)
- Take Profit: 40 pips (regular) or 3 ATR (prop firm)

## Risk Management

### Position Sizing
- **Regular Bot**: Based on pip value and account balance
- **Prop Firm Bot**: Conservative sizing based on ATR and risk limits

### Risk Limits
The bots automatically stop trading when:
- Daily loss limit is exceeded
- Overall loss limit is exceeded
- Connection to MT5 is lost

## Monitoring

### Logging
All bot activities are logged to:
- Console output
- `mt5_bots.log` file

### Status Monitoring
```python
# Get bot status
status = bot.get_status()
print(status)
```

## File Structure

```
mt5/
├── __init__.py              # Module initialization
├── mt5_config.py           # Configuration and connection management
├── mt5_trading_bot.py      # Regular trading bot
├── mt5_prop_firm_bot.py    # Prop firm trading bot with backtesting
├── run_mt5_bots.py         # Launcher script
└── README.md               # This file
```

## Safety Features

1. **Automatic Risk Limits**: Bots stop trading when risk limits are exceeded
2. **Connection Monitoring**: Automatic detection of connection issues
3. **Graceful Shutdown**: Proper cleanup on exit
4. **Error Handling**: Comprehensive error handling and logging
5. **Position Limits**: Maximum concurrent positions enforced

## Important Notes

1. **MT5 Terminal**: Ensure MetaTrader5 terminal is running and logged in
2. **Account Access**: Verify account credentials and permissions
3. **Market Hours**: Bots operate during market hours only
4. **Risk Warning**: Trading involves risk of loss
5. **Testing**: Always test on demo accounts first

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check MT5 terminal is running
   - Verify account credentials
   - Check internet connection

2. **No Trades Executed**
   - Check market hours
   - Verify signal conditions
   - Check risk limits

3. **Position Sizing Issues**
   - Check account balance
   - Verify symbol information
   - Check pip value calculations

### Debug Mode
Enable debug logging by modifying the logging level in the launcher script.

## License

This module is part of the trading bot project and follows the same license terms. 