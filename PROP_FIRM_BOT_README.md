# Prop Firm Trading Bot

A separate trading bot specifically designed for prop firm accounts, using the exact same strategy as `single_test.py` but with configurable risk parameters. **Now supports both backtesting and live trading on MT5!**

## 🎯 Overview

The Prop Firm Bot is built to:
- Use the **exact same strategy** as `single_test.py` (mean reversion with leverage and risk compounding)
- Have **configurable risk parameters** specifically for prop firm requirements
- Support **independent configuration** from the main trading bot
- Provide **comprehensive backtesting** with the same logic as `single_test.py`
- **Live trading on MT5** with real-time order placement

## 🔐 Account Credentials

**Default Prop Firm Account:**
- **Server**: ACGMarkets-Main
- **Login**: 2194718
- **Password**: vUD&V86dwc

## 📊 Trading Symbols

The bot uses different symbols for backtesting vs live trading:

| Type | Symbols | Description |
|------|---------|-------------|
| **Backtest** | `EURAUD=X`, `EURCAD=X` | Yahoo Finance symbols for backtesting |
| **Live Trading** | `EURAUD.pro`, `EURCAD.pro` | MT5 symbols for live trading |

## 📊 Strategy Parameters (Same as single_test.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lookback_window` | 30 | Lookback window for SMA calculation |
| `threshold` | 0.01 (1%) | Signal threshold for mean reversion |
| `position_size_pct` | 0.02 (2%) | Position size as percentage of capital |
| `stop_loss_pct` | 0.05 (5%) | Stop loss percentage |
| `take_profit_pct` | 0.10 (10%) | Take profit percentage |

## 🛡️ Risk Management (Configurable)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_loss_per_trade` | 0.01 (1%) | Maximum loss per individual trade |
| `max_daily_loss` | 0.02 (2%) | Maximum daily loss limit |
| `max_overall_loss` | 0.04 (4%) | Maximum overall loss limit |
| `max_positions` | 10 | Maximum concurrent positions |

## ⚙️ Leverage Settings (Same as single_test.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_leverage` | 1.0 (1:1) | Base leverage ratio |
| `max_leverage` | 5.0 (1:5) | Maximum leverage ratio |
| `risk_compounding` | True | Enable risk compounding |
| `enable_dynamic_leverage` | True | Enable dynamic leverage based on streaks |
| `winning_streak_threshold` | 3 | Threshold for increasing leverage |
| `losing_streak_threshold` | 2 | Threshold for decreasing leverage |

## 🚀 Usage

### Quick Start

1. **Run backtest with default settings:**
   ```bash
   python run_prop_firm_bot.py --backtest
   ```

2. **Show current configuration:**
   ```bash
   python run_prop_firm_bot.py --show-config
   ```

3. **Test MT5 connection:**
   ```bash
   python run_prop_firm_bot.py --test-connection
   ```

4. **Open interactive configuration:**
   ```bash
   python run_prop_firm_bot.py --config
   ```

### Advanced Usage

1. **Run backtest with custom parameters:**
   ```bash
   python run_prop_firm_bot.py --backtest --timeframe 2y --balance 50000
   ```

2. **Update specific parameter:**
   ```bash
   python run_prop_firm_bot.py --update max_daily_loss 0.03
   python run_prop_firm_bot.py --update live_symbols "EURAUD.pro,EURCAD.pro"
   ```

3. **Use configuration manager:**
   ```bash
   python prop_firm_config_manager.py
   ```

### Live Trading

**⚠️ WARNING: Live trading places real orders on your MT5 account!**

1. **Test MT5 connection first:**
   ```bash
   python run_prop_firm_bot.py --test-connection
   ```

2. **Start live trading:**
   ```bash
   python run_prop_firm_bot.py --live
   ```

3. **Update live trading symbols:**
   ```bash
   python run_prop_firm_bot.py --update live_symbols "EURAUD.pro,EURCAD.pro,GBPAUD.pro"
   ```

## 📁 Files

| File | Description |
|------|-------------|
| `prop_firm_bot.py` | Main prop firm bot implementation with MT5 integration |
| `prop_firm_config_manager.py` | Interactive configuration manager |
| `run_prop_firm_bot.py` | Command-line launcher with live trading support |
| `prop_firm_config.json` | Configuration file (auto-generated) |

## 🔧 Configuration

### Interactive Configuration

Run the configuration manager for a user-friendly interface:
```bash
python prop_firm_config_manager.py
```

Options:
1. **Display Current Configuration** - Show all current settings
2. **Interactive Configuration** - Step-by-step configuration
3. **Update Specific Parameter** - Update individual parameters
4. **Reset to Defaults** - Reset all settings to defaults
5. **Run Backtest** - Execute backtest with current settings
6. **Exit** - Exit the configuration manager

### Command-Line Configuration

Update parameters directly from command line:
```bash
# Update risk parameters
python run_prop_firm_bot.py --update max_loss_per_trade 0.015
python run_prop_firm_bot.py --update max_daily_loss 0.025
python run_prop_firm_bot.py --update max_overall_loss 0.05

# Update strategy parameters
python run_prop_firm_bot.py --update threshold 0.015
python run_prop_firm_bot.py --update position_size_pct 0.025

# Update symbols
python run_prop_firm_bot.py --update backtest_symbols "EURAUD=X,EURCAD=X,GBPAUD=X"
python run_prop_firm_bot.py --update live_symbols "EURAUD.pro,EURCAD.pro,GBPAUD.pro"

# Update leverage settings
python run_prop_firm_bot.py --update max_leverage 3.0
python run_prop_firm_bot.py --update risk_compounding False

# Update live trading settings
python run_prop_firm_bot.py --update enable_live_trading True
python run_prop_firm_bot.py --update demo_account True
```

## 📈 Backtesting

The prop firm bot uses the **exact same backtesting logic** as `single_test.py`:

### Features
- **Mean Reversion Strategy**: Based on Simple Moving Average (SMA)
- **Leverage and Risk Compounding**: Dynamic position sizing
- **Streak-Based Leverage**: Adjusts leverage based on win/loss streaks
- **Margin Call Simulation**: Realistic risk modeling
- **Comprehensive Metrics**: Sharpe ratio, drawdown, win rate, etc.

### Example Results
```
💰 BALANCE SUMMARY:
   Initial Balance: $100,000.00
   Final Balance: $238,544.59
   Balance Change: $138,544.59
   Total Return: $138,668.59
   Return Percentage: 138.67%

📈 TRADING PERFORMANCE:
   Total Trades: 88
   Winning Trades: 88
   Losing Trades: 0
   Win Percentage: 100.00%
   Average Trade Return: $1,575.78
   Best Trade: $3,442.94
   Worst Trade: $102.16
   Average Holding Period: 5.0 days

⚠️ RISK METRICS:
   Maximum Drawdown: 0.20%
   Sharpe Ratio: 10.30
```

## 🚀 Live Trading

### MT5 Integration

The prop firm bot now supports live trading on MetaTrader 5:

#### Features
- **Real-time Order Placement**: Places actual orders on MT5
- **Symbol Validation**: Checks if symbols are available on the server
- **Account Information**: Displays balance, equity, and margin
- **Position Management**: Monitors and manages open positions
- **Risk Management**: Enforces stop loss and take profit levels

#### Requirements
1. **MetaTrader 5 Terminal**: Must be installed and running
2. **Valid Account**: Demo or live account with the provided credentials
3. **Symbol Availability**: Trading symbols must be available on the server
4. **Internet Connection**: Required for real-time data and order execution

#### Setup Process
1. **Install MetaTrader 5** on your computer
2. **Login** with the provided credentials (2194718 / vUD&V86dwc)
3. **Test Connection** using `--test-connection`
4. **Verify Symbols** are available on the server
5. **Start Live Trading** with `--live`

#### Safety Features
- **Confirmation Prompt**: Requires user confirmation before starting live trading
- **Symbol Validation**: Checks symbol availability before placing orders
- **Error Handling**: Graceful handling of connection and order errors
- **Graceful Shutdown**: Proper cleanup on exit

### Live Trading Process

1. **Connection**: Connects to MT5 terminal
2. **Symbol Check**: Validates trading symbols are available
3. **Account Info**: Retrieves account balance and equity
4. **Trading Loop**: 
   - Monitors current positions
   - Generates signals using historical data
   - Places orders when signals are generated
   - Manages stop loss and take profit
5. **Continuous Monitoring**: Runs until manually stopped

## 🔄 Strategy Logic

The prop firm bot uses the exact same strategy as `single_test.py`:

1. **Signal Generation**:
   - Calculate SMA using `lookback_window`
   - Generate BUY signal when price < SMA * (1 - threshold)
   - Generate SELL signal when price > SMA * (1 + threshold)

2. **Position Management**:
   - Apply dynamic leverage based on win/loss streaks
   - Use risk compounding for position sizing
   - Exit positions at stop loss or take profit levels

3. **Risk Management**:
   - Enforce max loss per trade limit
   - Enforce max daily loss limit
   - Enforce max overall loss limit
   - Simulate margin call effects

## ⚠️ Important Notes

1. **Same Strategy**: The prop firm bot uses the exact same strategy logic as `single_test.py`
2. **Configurable Risk**: Risk parameters can be adjusted for prop firm requirements
3. **Independent Configuration**: Settings are separate from the main trading bot
4. **Realistic Simulation**: Includes leverage risk and margin call effects
5. **Comprehensive Testing**: Full backtesting with detailed metrics
6. **Live Trading**: Supports real-time trading on MT5 with proper risk management

## 🛠️ Customization

### Adding New Symbols

**For Backtesting:**
```bash
python run_prop_firm_bot.py --update backtest_symbols "EURAUD=X,EURCAD=X,GBPAUD=X,AUDCAD=X"
```

**For Live Trading:**
```bash
python run_prop_firm_bot.py --update live_symbols "EURAUD.pro,EURCAD.pro,GBPAUD.pro,AUDCAD.pro"
```

### Adjusting Risk Parameters
```bash
# More conservative
python run_prop_firm_bot.py --update max_loss_per_trade 0.005
python run_prop_firm_bot.py --update max_daily_loss 0.015
python run_prop_firm_bot.py --update max_overall_loss 0.03

# More aggressive
python run_prop_firm_bot.py --update max_loss_per_trade 0.02
python run_prop_firm_bot.py --update max_daily_loss 0.04
python run_prop_firm_bot.py --update max_overall_loss 0.08
```

### Modifying Strategy Parameters
```bash
# More sensitive signals
python run_prop_firm_bot.py --update threshold 0.005

# Larger positions
python run_prop_firm_bot.py --update position_size_pct 0.03

# Tighter stops
python run_prop_firm_bot.py --update stop_loss_pct 0.03
python run_prop_firm_bot.py --update take_profit_pct 0.06
```

## 🔌 MT5 Connection Troubleshooting

### Common Issues

1. **"Terminal: Authorization failed"**
   - Check if MT5 terminal is running
   - Verify login credentials are correct
   - Ensure account is active

2. **"Symbol not available"**
   - Check if symbols exist on the server
   - Verify symbol names (case-sensitive)
   - Contact broker for symbol availability

3. **"Connection timeout"**
   - Check internet connection
   - Verify MT5 terminal is connected to server
   - Restart MT5 terminal

### Testing Connection
```bash
python run_prop_firm_bot.py --test-connection
```

This will:
- Test MT5 initialization
- Attempt login with credentials
- Display account information
- List available symbols
- Check if your symbols are available

## 📞 Support

For questions or issues with the prop firm bot:
1. Check the configuration with `--show-config`
2. Test MT5 connection with `--test-connection`
3. Run a backtest to verify settings
4. Use the interactive configuration manager for easy setup
5. Compare results with `single_test.py` to ensure consistency
6. Check MT5 terminal for connection and symbol issues 