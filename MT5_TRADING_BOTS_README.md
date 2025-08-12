# MT5 Trading Bots System

## Overview

This system provides separate MT5 trading bots for regular and prop firm accounts with configurable parameters and comprehensive backtesting capabilities. The bots use mean reversion strategies with advanced filtering and risk management.

## 🎯 Key Features

- **Separate Configurations**: Different parameters for regular and prop firm accounts
- **Configurable Risk Management**: Adjustable daily/overall loss limits
- **Advanced Filtering**: Volatility, trend, and momentum filters
- **Backtesting**: YFinance-based backtesting with detailed results
- **Live Trading**: MT5 integration for live trading
- **Symbol Management**: EURCAD and EURAUD for both backtesting and live trading

## 📊 Trading Symbols

### Backtesting (YFinance)
- **EURCAD=X** - Euro to Canadian Dollar
- **EURAUD=X** - Euro to Australian Dollar

### Live Trading (MT5)
- **EURCAD.pro** - Euro to Canadian Dollar (live)
- **EURAUD.pro** - Euro to Australian Dollar (live)

## 🏢 Account Configurations

### Regular Account
- **Server**: Demo (configurable)
- **Login**: 123456 (configurable)
- **Password**: demo (configurable)
- **Risk Profile**: More aggressive
- **Position Size**: 2% per trade
- **Max Daily Loss**: 5%
- **Max Overall Loss**: 10%
- **Max Positions**: 10

### Prop Firm Account
- **Server**: ACGMarkets-Main
- **Login**: 2194718
- **Password**: vUD&V86dwc
- **Risk Profile**: Conservative
- **Position Size**: 1% per trade
- **Max Daily Loss**: 4%
- **Max Overall Loss**: 4%
- **Max Positions**: 3

## 📈 Strategy Details

### Mean Reversion Strategy
- **Entry**: Price 0.5% below/above SMA20
- **Exit**: Stop loss and take profit levels
- **Filters**: Volatility, trend, and momentum confirmation

### Prop Firm Enhancements
- **Signal Confirmation**: 2 periods required
- **Volatility Filter**: Minimum ATR threshold
- **Trend Filter**: SMA50 trend confirmation
- **Momentum Filter**: RSI oversold/overbought levels
- **Time Filter**: Session-based trading (08:00-16:00)
- **News Avoidance**: Skip high-impact news events

## 🛡️ Risk Management

### Conservative Settings (Prop Firm)
- **Dynamic Position Sizing**: Adjust based on volatility
- **Kelly Criterion**: Optimal position sizing
- **Correlation Limit**: 0.5 (avoid correlated positions)
- **Trailing Stops**: Dynamic profit protection
- **Breakeven Triggers**: Move stop loss to breakeven

### Risk Limits
- **Daily Loss Limit**: 4% (configurable)
- **Overall Loss Limit**: 4% (configurable)
- **Max Drawdown**: 10%
- **Margin Level**: 200% minimum

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test Configuration
```bash
python test_mt5_setup.py
```

### 3. Show Current Configurations
```bash
python mt5_launcher.py --show-config
```

### 4. Run Backtest
```bash
python mt5_launcher.py --backtest
```

### 5. Configure Parameters (Interactive)
```bash
python mt5_launcher.py --config
```

## 📋 Available Commands

### Configuration
```bash
# Show current configurations
python mt5_launcher.py --show-config

# Interactive configuration
python mt5_launcher.py --config
```

### Backtesting
```bash
# Run prop firm backtest
python mt5_launcher.py --backtest

# Run regular account backtest
python mt5_launcher.py --backtest-regular

# Custom date range
python mt5_launcher.py --backtest --start-date 2024-06-01 --end-date 2024-12-31
```

### Live Trading
```bash
# Run regular bot
python mt5_launcher.py --regular

# Run prop firm bot
python mt5_launcher.py --prop-firm

# Run both bots
python mt5_launcher.py --both

# Run with monitoring
python mt5_launcher.py --both --monitor
```

## 🔧 Configuration Options

### Strategy Parameters
- **Lookback Window**: Periods for SMA calculation (default: 30)
- **Threshold**: Deviation percentage for signals (default: 0.5%)
- **Position Size**: Percentage of capital per trade
- **Stop Loss**: Percentage loss to exit position
- **Take Profit**: Percentage gain to exit position
- **Max Positions**: Maximum concurrent trades

### Risk Management
- **Max Daily Loss**: Daily loss limit (default: 4%)
- **Max Overall Loss**: Total loss limit (default: 4%)
- **Max Drawdown**: Maximum drawdown before stopping
- **Correlation Limit**: Maximum correlation between positions

### Advanced Filters
- **Signal Confirmation**: Number of confirmation periods
- **Volatility Filter**: Minimum ATR threshold
- **Trend Filter**: SMA/EMA trend confirmation
- **Momentum Filter**: RSI/Stochastic momentum
- **Time Filter**: Session-based trading
- **News Avoidance**: Skip news events

## 📊 Backtest Results Example

```
============================================================
BACKTEST RESULTS - PROP FIRM ACCOUNT
============================================================

📊 Overall Performance:
   Initial Capital: $100,000.00
   Final Capital: $100,133.26
   Total Return: $133.26
   Total Trades: 6
   Winning Trades: 3
   Losing Trades: 3
   Win Rate: 50.00%

📈 Strategy Details:
   Account Type: PROP FIRM
   Backtest Symbols: EURCAD=X, EURAUD=X
   Live Trading Symbols: EURCAD.pro, EURAUD.pro
   Strategy: Mean Reversion with Filters
   Risk Management: Conservative (4% daily/overall loss limits)

🔍 Symbol Results:
   EURCAD=X: 2 trades, 0.0% win rate, $-28.07 P&L
   EURAUD=X: 4 trades, 75.0% win rate, $161.33 P&L
```

## ⚙️ File Structure

```
trading_bot/
├── mt5_config.py              # Configuration management
├── mt5_regular_bot.py         # Regular account trading bot
├── mt5_prop_firm_bot.py       # Prop firm trading bot
├── mt5_launcher.py            # Main launcher script
├── test_mt5_setup.py          # Test and verification script
├── requirements.txt           # Python dependencies
└── MT5_TRADING_BOTS_README.md # This file
```

## 🔐 Security Notes

- **Environment Variables**: Use `.env` file for sensitive credentials
- **Demo Testing**: Always test with demo accounts first
- **Risk Limits**: Never exceed your risk tolerance
- **Monitoring**: Monitor bots regularly during live trading

## 📈 Performance Optimization

### Prop Firm Bot Features
- **Automatic Optimization**: Parameter adjustment based on performance
- **Sortino Ratio**: Risk-adjusted performance metric
- **Dynamic Position Sizing**: Adjust based on volatility
- **Kelly Criterion**: Optimal position sizing

### Conservative Approach
- **Lower Position Sizes**: 1% vs 2% for regular account
- **Stricter Filters**: More confirmation required
- **Tighter Risk Limits**: 4% vs 5% daily loss
- **Fewer Positions**: 3 vs 10 maximum positions

## 🚨 Important Warnings

1. **Demo First**: Always test with demo accounts before live trading
2. **Risk Management**: Never risk more than you can afford to lose
3. **Monitoring**: Monitor bots regularly during live trading
4. **Market Conditions**: Strategy performance varies with market conditions
5. **Backtesting**: Past performance doesn't guarantee future results

## 🔧 Troubleshooting

### Common Issues
1. **MT5 Connection**: Ensure MT5 is running and logged in
2. **Symbol Not Found**: Check symbol names and availability
3. **Permission Errors**: Run MT5 as administrator
4. **Data Issues**: Verify internet connection for YFinance data

### Support
- Check logs in `mt5_bots.log`
- Verify MT5 terminal settings
- Test with demo accounts first
- Review configuration parameters

## 📞 Support and Updates

For support or questions:
1. Check the configuration with `--show-config`
2. Run tests with `test_mt5_setup.py`
3. Review logs for error details
4. Test with demo accounts first

## 🎯 Next Steps

1. **Test Configuration**: Run `python test_mt5_setup.py`
2. **Review Settings**: Use `python mt5_launcher.py --show-config`
3. **Run Backtest**: Use `python mt5_launcher.py --backtest`
4. **Configure Parameters**: Use `python mt5_launcher.py --config`
5. **Demo Trading**: Test with demo accounts
6. **Live Trading**: Start with small positions

---

**Disclaimer**: This system is for educational purposes. Trading involves risk and past performance doesn't guarantee future results. Always test thoroughly and never risk more than you can afford to lose. 