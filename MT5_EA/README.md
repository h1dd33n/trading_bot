# MT5 Expert Advisors - Trading Bots

This folder contains MQL5 Expert Advisors (EAs) that implement the same trading strategy as the Python bots, but as native MetaTrader 5 Expert Advisors.

## 📁 Files

- **`PropFirmBot.mq5`** - Prop Firm Trading Bot with strict risk management
- **`RegularBot.mq5`** - Regular Trading Bot with standard risk parameters
- **`README.md`** - This documentation file

## 🚀 Installation

### Step 1: Copy Files to MT5
1. Copy the `.mq5` files to your MetaTrader 5 `Experts` folder:
   ```
   C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Experts\
   ```

### Step 2: Compile the EAs
1. Open MetaTrader 5
2. Press `Ctrl+N` to open the Navigator
3. Go to `Expert Advisors` tab
4. Right-click on the EA and select `Modify`
5. Press `F7` to compile
6. Ensure there are no compilation errors

### Step 3: Enable Automated Trading
1. Go to `Tools` → `Options` → `Expert Advisors`
2. Enable:
   - ✅ `Allow automated trading`
   - ✅ `Allow DLL imports`
   - ✅ `Allow WebRequest for listed URL`
3. Click `OK` and restart MT5

## 🤖 Expert Advisors

### PropFirmBot.mq5
**Purpose**: Designed for prop firm accounts with strict risk management

**Key Features**:
- **Strict Risk Limits**: 1% max loss per trade, 2% daily loss, 4% overall loss
- **Mean Reversion Strategy**: Based on Simple Moving Average
- **Position Sizing**: 2% of account balance per trade
- **Stop Loss**: 5% of entry price
- **Take Profit**: 10% of entry price

**Default Parameters**:
```
Trading Parameters:
- Threshold: 1.0% (signal generation)
- Lookback Window: 30 (MA calculation)
- Position Size: 2.0% (of balance)
- Stop Loss: 5.0% (of price)
- Take Profit: 10.0% (of price)

Risk Management:
- Max Loss Per Trade: 1.0%
- Max Daily Loss: 2.0%
- Max Overall Loss: 4.0%
- Magic Number: 234000
```

### RegularBot.mq5
**Purpose**: Standard trading bot with more relaxed risk parameters

**Key Features**:
- **Standard Risk Limits**: 2% max loss per trade, 5% daily loss, 10% overall loss
- **Same Strategy**: Mean reversion based on Simple Moving Average
- **Flexible Position Sizing**: 2% of account balance per trade
- **Configurable Risk**: Higher risk tolerance than prop firm version

**Default Parameters**:
```
Trading Parameters:
- Threshold: 1.0% (signal generation)
- Lookback Window: 30 (MA calculation)
- Position Size: 2.0% (of balance)
- Stop Loss: 5.0% (of price)
- Take Profit: 10.0% (of price)

Risk Management:
- Max Loss Per Trade: 2.0%
- Max Daily Loss: 5.0%
- Max Overall Loss: 10.0%
- Magic Number: 234001
```

## 📊 Strategy Logic

Both EAs implement the same **Mean Reversion Strategy**:

### Signal Generation
```mql5
// Mean reversion logic
if(currentPrice < ma * (1 - threshold))
{
    return "BUY";  // Price below MA - buy signal
}
else if(currentPrice > ma * (1 + threshold))
{
    return "SELL"; // Price above MA - sell signal
}
return "HOLD";     // No signal
```

### Moving Average Calculation
- **Type**: Simple Moving Average (SMA)
- **Period**: 30 days (configurable)
- **Data**: Daily close prices

## ⚙️ Configuration

### Trading Parameters
- **`InpThreshold`**: Threshold for signal generation (0.01 = 1%)
- **`InpLookbackWindow`**: Period for MA calculation (default: 30)
- **`InpPositionSizePct`**: Position size as % of balance (0.02 = 2%)
- **`InpStopLossPct`**: Stop loss as % of price (0.05 = 5%)
- **`InpTakeProfitPct`**: Take profit as % of price (0.10 = 10%)

### Risk Management
- **`InpMaxLossPerTrade`**: Maximum loss per individual trade
- **`InpMaxDailyLoss`**: Maximum daily loss limit
- **`InpMaxOverallLoss`**: Maximum overall account loss limit
- **`InpEnableRiskCompounding`**: Enable/disable risk compounding
- **`InpLeverageMultiplier`**: Leverage multiplier for position sizing

### Advanced Settings
- **`InpMagicNumber`**: Unique identifier for EA orders
- **`InpSlippage`**: Maximum allowed slippage in points
- **`InpEnableTrailingStop`**: Enable trailing stop functionality
- **`InpTrailingStopPct`**: Trailing stop percentage
- **`InpEnableBreakeven`**: Enable breakeven trigger
- **`InpBreakevenTrigger`**: Breakeven trigger percentage

## 🎯 Usage

### Step 1: Attach EA to Chart
1. Open a chart for your desired symbol (e.g., EURAUD, USDAUD)
2. Drag the EA from Navigator to the chart
3. Configure parameters in the popup dialog
4. Click `OK`

### Step 2: Monitor Performance
- **Journal Tab**: View EA logs and trade information
- **Experts Tab**: Monitor EA status and performance
- **Terminal Tab**: View account balance and equity changes

### Step 3: Risk Management
The EA automatically implements:
- **Position Limits**: Only one position at a time
- **Loss Limits**: Stops trading when limits are reached
- **Stop Loss/Take Profit**: Automatic order management
- **Trailing Stop**: Optional trailing stop functionality
- **Breakeven**: Optional breakeven trigger

## 🔧 Customization

### Modifying Risk Parameters
```mql5
// For more conservative trading
InpMaxLossPerTrade = 0.005;    // 0.5% per trade
InpMaxDailyLoss = 0.01;        // 1% daily
InpMaxOverallLoss = 0.02;      // 2% overall

// For more aggressive trading
InpMaxLossPerTrade = 0.03;     // 3% per trade
InpMaxDailyLoss = 0.08;        // 8% daily
InpMaxOverallLoss = 0.15;      // 15% overall
```

### Adjusting Strategy Parameters
```mql5
// More sensitive signals
InpThreshold = 0.005;          // 0.5% threshold

// Less sensitive signals
InpThreshold = 0.02;           // 2% threshold

// Different MA period
InpLookbackWindow = 50;        // 50-day MA
```

## 📈 Performance Monitoring

### Key Metrics to Track
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Total Return**: Overall account growth

### Log Messages
The EA provides detailed logging:
```
✅ Prop Firm Bot initialized successfully
💰 Initial Balance: $50,000.00
📊 Symbol: EURAUD
⚙️  Threshold: 1.0%
📈 Position Size: 2.0%

✅ Position opened: BUY 0.10 lots at 1.78952
   Stop Loss: 1.70004
   Take Profit: 1.96847

🎯 Breakeven triggered for ticket: 12345678
```

## ⚠️ Important Notes

### Risk Warnings
- **Past performance does not guarantee future results**
- **Always test on demo accounts first**
- **Monitor the EA regularly**
- **Understand the strategy before using real money**

### Technical Requirements
- **MetaTrader 5** (latest version)
- **Automated trading enabled**
- **Stable internet connection**
- **Adequate account balance**

### Best Practices
1. **Start Small**: Use small position sizes initially
2. **Monitor Closely**: Check EA performance regularly
3. **Backup Settings**: Save your parameter configurations
4. **Test Thoroughly**: Use demo accounts for testing
5. **Risk Management**: Never risk more than you can afford to lose

## 🛠️ Troubleshooting

### Common Issues

**EA Not Trading**
- Check if automated trading is enabled
- Verify symbol is tradeable
- Check account balance and margin
- Review risk management limits

**Compilation Errors**
- Ensure MQL5 syntax is correct
- Check for missing semicolons or brackets
- Verify all functions are properly defined

**Connection Issues**
- Check internet connection
- Verify broker server status
- Restart MetaTrader 5

### Error Messages
```
❌ Invalid input parameters
❌ Trading is not allowed for symbol: EURAUD
❌ Failed to open position. Error: 10026 - AutoTrading disabled
⚠️  Daily loss limit reached: $1,000.00
```

## 📞 Support

For issues or questions:
1. Check the **Journal** tab for error messages
2. Review this documentation
3. Test on demo accounts first
4. Contact your broker for technical issues

## 🔄 Updates

Keep your EAs updated:
1. Check for new versions regularly
2. Test updates on demo accounts
3. Backup your current settings
4. Monitor performance after updates

---

**Disclaimer**: This software is for educational purposes. Trading involves risk and may not be suitable for all investors. Always test thoroughly before using with real money. 