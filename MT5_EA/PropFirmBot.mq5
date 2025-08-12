//+------------------------------------------------------------------+
//|                                              PropFirmBot.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Prop Firm Trading Bot - Mean Reversion Strategy"

//--- Input Parameters
input group "=== Trading Parameters ==="
input double   InpThreshold = 0.01;           // Threshold for signal generation (1%)
input int      InpLookbackWindow = 30;        // Lookback window for MA calculation
input double   InpPositionSizePct = 0.02;     // Position size as % of balance (2%)
input double   InpStopLossPct = 0.05;         // Stop loss as % of price (5%)
input double   InpTakeProfitPct = 0.10;       // Take profit as % of price (10%)

input group "=== Risk Management ==="
input double   InpMaxLossPerTrade = 0.01;     // Max loss per trade (1%)
input double   InpMaxDailyLoss = 0.02;        // Max daily loss (2%)
input double   InpMaxOverallLoss = 0.04;      // Max overall loss (4%)
input bool     InpEnableRiskCompounding = true; // Enable risk compounding
input double   InpLeverageMultiplier = 1.0;   // Leverage multiplier

input group "=== Advanced Settings ==="
input int      InpMagicNumber = 234000;       // Magic number for orders
input int      InpSlippage = 20;              // Slippage in points
input bool     InpEnableTrailingStop = false; // Enable trailing stop
input double   InpTrailingStopPct = 0.02;     // Trailing stop percentage
input bool     InpEnableBreakeven = false;    // Enable breakeven trigger
input double   InpBreakevenTrigger = 0.01;    // Breakeven trigger percentage

//--- Global Variables
double g_initialBalance = 0;
double g_dailyLoss = 0;
double g_overallLoss = 0;
datetime g_lastTradeTime = 0;
int g_winStreak = 0;
int g_loseStreak = 0;
double g_currentLeverage = 1.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize global variables
    g_initialBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    g_dailyLoss = 0;
    g_overallLoss = 0;
    g_lastTradeTime = 0;
    g_winStreak = 0;
    g_loseStreak = 0;
    g_currentLeverage = InpLeverageMultiplier;
    
    // Validate input parameters
    if(!ValidateInputs())
    {
        Print("❌ Invalid input parameters");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    // Check if symbol is available
    if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
    {
        Print("❌ Trading is not allowed for symbol: ", _Symbol);
        return INIT_FAILED;
    }
    
    Print("✅ Prop Firm Bot initialized successfully");
    Print("💰 Initial Balance: $", DoubleToString(g_initialBalance, 2));
    Print("📊 Symbol: ", _Symbol);
    Print("⚙️  Threshold: ", DoubleToString(InpThreshold * 100, 1), "%");
    Print("📈 Position Size: ", DoubleToString(InpPositionSizePct * 100, 1), "%");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 Prop Firm Bot deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if we should trade
    if(!ShouldTrade())
        return;
    
    // Check for exit signals on existing positions
    CheckExitSignals();
    
    // Check for new entry signals
    CheckEntrySignals();
}

//+------------------------------------------------------------------+
//| Check if we should trade based on risk management               |
//+------------------------------------------------------------------+
bool ShouldTrade()
{
    // Check if market is closed
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
        return false;
    
    // Check if we have open positions
    if(PositionsTotal() > 0)
        return false;
    
    // Check daily loss limit
    double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double dailyLoss = g_initialBalance - currentBalance;
    if(dailyLoss >= g_initialBalance * InpMaxDailyLoss)
    {
        Print("⚠️  Daily loss limit reached: $", DoubleToString(dailyLoss, 2));
        return false;
    }
    
    // Check overall loss limit
    double overallLoss = g_initialBalance - currentBalance;
    if(overallLoss >= g_initialBalance * InpMaxOverallLoss)
    {
        Print("⚠️  Overall loss limit reached: $", DoubleToString(overallLoss, 2));
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check for exit signals on existing positions                    |
//+------------------------------------------------------------------+
void CheckExitSignals()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket <= 0)
            continue;
        
        if(!PositionSelectByTicket(ticket))
            continue;
        
        // Check if position is for this symbol
        if(PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;
        
        // Check trailing stop
        if(InpEnableTrailingStop)
            CheckTrailingStop(ticket);
        
        // Check breakeven
        if(InpEnableBreakeven)
            CheckBreakeven(ticket);
    }
}

//+------------------------------------------------------------------+
//| Check for new entry signals                                     |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
    // Get current price
    double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    
    // Calculate moving average
    double ma = CalculateMA(InpLookbackWindow);
    
    if(ma <= 0)
        return;
    
    // Generate signal
    string signal = GenerateSignal(currentPrice, ma);
    
    if(signal == "BUY")
    {
        OpenPosition(ORDER_TYPE_BUY, currentPrice);
    }
    else if(signal == "SELL")
    {
        OpenPosition(ORDER_TYPE_SELL, currentPrice);
    }
}

//+------------------------------------------------------------------+
//| Generate trading signal based on mean reversion strategy        |
//+------------------------------------------------------------------+
string GenerateSignal(double currentPrice, double ma)
{
    double threshold = InpThreshold;
    
    // Mean reversion logic
    if(currentPrice < ma * (1 - threshold))
    {
        return "BUY";
    }
    else if(currentPrice > ma * (1 + threshold))
    {
        return "SELL";
    }
    
    return "HOLD";
}

//+------------------------------------------------------------------+
//| Calculate Simple Moving Average                                 |
//+------------------------------------------------------------------+
double CalculateMA(int period)
{
    double ma = 0;
    int count = 0;
    
    for(int i = 0; i < period; i++)
    {
        double close = iClose(_Symbol, PERIOD_D1, i);
        if(close > 0)
        {
            ma += close;
            count++;
        }
    }
    
    if(count > 0)
        return ma / count;
    
    return 0;
}

//+------------------------------------------------------------------+
//| Open a new position                                             |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE orderType, double price)
{
    // Calculate position size
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double positionSize = balance * InpPositionSizePct * g_currentLeverage;
    
    // Convert to lots
    double lotSize = NormalizeDouble(positionSize / (price * 100000), 2);
    
    // Ensure minimum lot size
    double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    
    lotSize = MathMax(lotSize, minLot);
    lotSize = MathMin(lotSize, maxLot);
    lotSize = NormalizeDouble(lotSize / lotStep, 2) * lotStep;
    
    // Calculate stop loss and take profit
    double sl = 0, tp = 0;
    
    if(orderType == ORDER_TYPE_BUY)
    {
        sl = price * (1 - InpStopLossPct);
        tp = price * (1 + InpTakeProfitPct);
    }
    else
    {
        sl = price * (1 + InpStopLossPct);
        tp = price * (1 - InpTakeProfitPct);
    }
    
    // Prepare trade request
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = _Symbol;
    request.volume = lotSize;
    request.type = orderType;
    request.price = price;
    request.sl = sl;
    request.tp = tp;
    request.deviation = InpSlippage;
    request.magic = InpMagicNumber;
    request.comment = "PropFirmBot";
    request.type_filling = ORDER_FILLING_IOC;
    
    // Send order
    bool success = OrderSend(request, result);
    
    if(success && result.retcode == TRADE_RETCODE_DONE)
    {
        Print("✅ Position opened: ", (orderType == ORDER_TYPE_BUY ? "BUY" : "SELL"), " ", DoubleToString(lotSize, 2), " lots at ", DoubleToString(price, _Digits));
        Print("   Stop Loss: ", DoubleToString(sl, _Digits));
        Print("   Take Profit: ", DoubleToString(tp, _Digits));
        
        g_lastTradeTime = TimeCurrent();
    }
    else
    {
        Print("❌ Failed to open position. Error: ", result.retcode, " - ", result.comment);
    }
}

//+------------------------------------------------------------------+
//| Check trailing stop for position                                |
//+------------------------------------------------------------------+
void CheckTrailingStop(ulong ticket)
{
    if(!PositionSelectByTicket(ticket))
        return;
    
    double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    
    double newSL = 0;
    bool shouldModify = false;
    
    if(posType == POSITION_TYPE_BUY)
    {
        double trailingPrice = currentPrice * (1 - InpTrailingStopPct);
        if(trailingPrice > currentSL && trailingPrice < currentPrice)
        {
            newSL = trailingPrice;
            shouldModify = true;
        }
    }
    else
    {
        double trailingPrice = currentPrice * (1 + InpTrailingStopPct);
        if(trailingPrice < currentSL && trailingPrice > currentPrice)
        {
            newSL = trailingPrice;
            shouldModify = true;
        }
    }
    
    if(shouldModify)
    {
        ModifyPosition(ticket, newSL, PositionGetDouble(POSITION_TP));
    }
}

//+------------------------------------------------------------------+
//| Check breakeven trigger for position                            |
//+------------------------------------------------------------------+
void CheckBreakeven(ulong ticket)
{
    if(!PositionSelectByTicket(ticket))
        return;
    
    double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
    
    double breakevenPrice = 0;
    bool shouldModify = false;
    
    if(posType == POSITION_TYPE_BUY)
    {
        double triggerPrice = openPrice * (1 + InpBreakevenTrigger);
        if(currentPrice >= triggerPrice && currentSL < openPrice)
        {
            breakevenPrice = openPrice;
            shouldModify = true;
        }
    }
    else
    {
        double triggerPrice = openPrice * (1 - InpBreakevenTrigger);
        if(currentPrice <= triggerPrice && currentSL > openPrice)
        {
            breakevenPrice = openPrice;
            shouldModify = true;
        }
    }
    
    if(shouldModify)
    {
        ModifyPosition(ticket, breakevenPrice, PositionGetDouble(POSITION_TP));
        Print("🎯 Breakeven triggered for ticket: ", ticket);
    }
}

//+------------------------------------------------------------------+
//| Modify position stop loss and take profit                       |
//+------------------------------------------------------------------+
void ModifyPosition(ulong ticket, double sl, double tp)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.symbol = _Symbol;
    request.sl = sl;
    request.tp = tp;
    
    bool success = OrderSend(request, result);
    
    if(success && result.retcode == TRADE_RETCODE_DONE)
    {
        Print("✅ Position modified: SL=", DoubleToString(sl, _Digits), " TP=", DoubleToString(tp, _Digits));
    }
    else
    {
        Print("❌ Failed to modify position. Error: ", result.retcode);
    }
}

//+------------------------------------------------------------------+
//| Validate input parameters                                       |
//+------------------------------------------------------------------+
bool ValidateInputs()
{
    if(InpThreshold <= 0 || InpThreshold > 0.1)
    {
        Print("❌ Invalid threshold: ", InpThreshold);
        return false;
    }
    
    if(InpLookbackWindow <= 0 || InpLookbackWindow > 1000)
    {
        Print("❌ Invalid lookback window: ", InpLookbackWindow);
        return false;
    }
    
    if(InpPositionSizePct <= 0 || InpPositionSizePct > 0.1)
    {
        Print("❌ Invalid position size: ", InpPositionSizePct);
        return false;
    }
    
    if(InpStopLossPct <= 0 || InpTakeProfitPct <= 0)
    {
        Print("❌ Invalid stop loss or take profit");
        return false;
    }
    
    return true;
}

 