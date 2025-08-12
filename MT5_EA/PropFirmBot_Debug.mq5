//+------------------------------------------------------------------+
//|                                        PropFirmBot_Debug.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Prop Firm Trading Bot - Debug Version"

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

input group "=== Debug Settings ==="
input bool     InpEnableDebug = true;         // Enable debug output
input int      InpDebugInterval = 10;         // Debug output every N ticks

//--- Global Variables
double g_initialBalance = 0;
double g_dailyLoss = 0;
double g_overallLoss = 0;
datetime g_lastTradeTime = 0;
int g_winStreak = 0;
int g_loseStreak = 0;
double g_currentLeverage = 1.0;
int g_tickCount = 0;

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
    g_tickCount = 0;
    
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
    
    // Check data availability
    int total_bars = Bars(_Symbol, PERIOD_D1);
    Print("📊 Total bars available: ", total_bars);
    
    if(total_bars < InpLookbackWindow)
    {
        Print("❌ ERROR: Insufficient data! Need at least ", InpLookbackWindow, " bars, but only have ", total_bars);
        return INIT_FAILED;
    }
    
    Print("✅ Prop Firm Bot Debug initialized successfully");
    Print("💰 Initial Balance: $", DoubleToString(g_initialBalance, 2));
    Print("📊 Symbol: ", _Symbol);
    Print("⚙️  Threshold: ", DoubleToString(InpThreshold * 100, 1), "%");
    Print("📈 Position Size: ", DoubleToString(InpPositionSizePct * 100, 1), "%");
    Print("🔍 Debug Mode: ", (InpEnableDebug ? "ON" : "OFF"));
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 Prop Firm Bot Debug deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    g_tickCount++;
    
    // Debug output every N ticks
    if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
    {
        Print("=== DEBUG TICK ", g_tickCount, " ===");
        Print("Symbol: ", _Symbol, " Time: ", TimeToString(TimeCurrent()));
    }
    
    // Check if we should trade
    if(!ShouldTrade())
    {
        if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
            Print("❌ ShouldTrade() returned false");
        return;
    }
    
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
    {
        if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
            Print("❌ Market closed - MQL_TRADE_ALLOWED = false");
        return false;
    }
    
    // Check if we have open positions
    if(PositionsTotal() > 0)
    {
        if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
            Print("❌ Already have ", PositionsTotal(), " open positions");
        return false;
    }
    
    // Check daily loss limit
    double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    double dailyLoss = g_initialBalance - currentBalance;
    if(dailyLoss >= g_initialBalance * InpMaxDailyLoss)
    {
        if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
            Print("⚠️  Daily loss limit reached: $", DoubleToString(dailyLoss, 2));
        return false;
    }
    
    // Check overall loss limit
    double overallLoss = g_initialBalance - currentBalance;
    if(overallLoss >= g_initialBalance * InpMaxOverallLoss)
    {
        if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
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
    // Not implemented in debug version
}

//+------------------------------------------------------------------+
//| Check for new entry signals                                     |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
    // Get current price
    double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    
    if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
        Print("📈 Current Price: ", DoubleToString(currentPrice, _Digits));
    
    // Calculate moving average
    double ma = CalculateMA(InpLookbackWindow);
    
    if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
        Print("📊 Moving Average: ", DoubleToString(ma, _Digits));
    
    if(ma <= 0)
    {
        if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
            Print("❌ Invalid MA value: ", ma);
        return;
    }
    
    // Generate signal
    string signal = GenerateSignal(currentPrice, ma);
    
    if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
        Print("🎯 Generated Signal: ", signal);
    
    if(signal == "BUY")
    {
        if(InpEnableDebug)
            Print("🟢 BUY Signal Generated - Opening Position");
        OpenPosition(ORDER_TYPE_BUY, currentPrice);
    }
    else if(signal == "SELL")
    {
        if(InpEnableDebug)
            Print("🔴 SELL Signal Generated - Opening Position");
        OpenPosition(ORDER_TYPE_SELL, currentPrice);
    }
    else if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
    {
        Print("⚪ HOLD Signal - No action");
    }
}

//+------------------------------------------------------------------+
//| Generate trading signal based on mean reversion strategy        |
//+------------------------------------------------------------------+
string GenerateSignal(double currentPrice, double ma)
{
    if(ma <= 0)
        return "NO_MA_DATA";
    
    double threshold = InpThreshold;
    
    if(InpEnableDebug && g_tickCount % InpDebugInterval == 0)
    {
        Print("🔍 Signal Analysis:");
        Print("   Current Price: ", DoubleToString(currentPrice, _Digits));
        Print("   MA: ", DoubleToString(ma, _Digits));
        Print("   Threshold: ", DoubleToString(threshold * 100, 1), "%");
        Print("   Buy Level: ", DoubleToString(ma * (1 - threshold), _Digits));
        Print("   Sell Level: ", DoubleToString(ma * (1 + threshold), _Digits));
    }
    
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
    if(InpEnableDebug)
        Print("🚀 Attempting to open position...");
    
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
    
    if(InpEnableDebug)
    {
        Print("📊 Position Details:");
        Print("   Balance: $", DoubleToString(balance, 2));
        Print("   Position Size: $", DoubleToString(positionSize, 2));
        Print("   Lot Size: ", DoubleToString(lotSize, 2));
        Print("   Min Lot: ", DoubleToString(minLot, 2));
        Print("   Max Lot: ", DoubleToString(maxLot, 2));
        Print("   Lot Step: ", DoubleToString(lotStep, 2));
    }
    
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
    
    if(InpEnableDebug)
    {
        Print("🎯 Order Details:");
        Print("   Type: ", (orderType == ORDER_TYPE_BUY ? "BUY" : "SELL"));
        Print("   Price: ", DoubleToString(price, _Digits));
        Print("   Stop Loss: ", DoubleToString(sl, _Digits));
        Print("   Take Profit: ", DoubleToString(tp, _Digits));
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
    request.deviation = 20;
    request.magic = 234000;
    request.comment = "PropFirmBotDebug";
    request.type_filling = ORDER_FILLING_IOC;
    
    // Send order
    bool success = OrderSend(request, result);
    
    if(success && result.retcode == TRADE_RETCODE_DONE)
    {
        Print("✅ Position opened successfully!");
        Print("   Ticket: ", result.order);
        Print("   Volume: ", DoubleToString(lotSize, 2));
        Print("   Price: ", DoubleToString(price, _Digits));
        
        g_lastTradeTime = TimeCurrent();
    }
    else
    {
        Print("❌ Failed to open position!");
        Print("   Error Code: ", result.retcode);
        Print("   Error Comment: ", result.comment);
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