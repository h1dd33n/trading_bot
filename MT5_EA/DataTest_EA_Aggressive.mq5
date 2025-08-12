//+------------------------------------------------------------------+
//|                                      DataTest_EA_Aggressive.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Data Availability Test EA - Aggressive Version"

//--- Input Parameters
input int      InpLookbackWindow = 20;        // Lookback window for MA calculation (shorter)
input double   InpThreshold = 0.005;          // Threshold for signal generation (0.5% - very sensitive)
input double   InpPositionSize = 0.01;        // Position size in lots
input double   InpStopLossPct = 0.02;         // Stop loss as % of price (2%)
input double   InpTakeProfitPct = 0.04;       // Take profit as % of price (4%)

//--- Global Variables
int g_tickCount = 0;
bool g_initialized = false;
datetime g_lastTradeTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    g_tickCount = 0;
    g_initialized = false;
    g_lastTradeTime = 0;
    
    Print("=== Data Availability Test EA - AGGRESSIVE VERSION ===");
    Print("Symbol: ", _Symbol);
    Print("Period: ", EnumToString(Period()));
    Print("Lookback Window: ", InpLookbackWindow, " (shorter for more sensitivity)");
    Print("Threshold: ", InpThreshold, " (", DoubleToString(InpThreshold * 100, 2), "%) - VERY SENSITIVE");
    Print("Position Size: ", InpPositionSize, " lots");
    Print("Stop Loss: ", DoubleToString(InpStopLossPct * 100, 1), "%");
    Print("Take Profit: ", DoubleToString(InpTakeProfitPct * 100, 1), "%");
    Print("");
    
    // Test data availability
    int total_bars = Bars(_Symbol, PERIOD_D1);
    Print("📊 Total bars available: ", total_bars);
    
    if(total_bars < InpLookbackWindow)
    {
        Print("❌ ERROR: Insufficient data! Need at least ", InpLookbackWindow, " bars, but only have ", total_bars);
        return INIT_FAILED;
    }
    
    // Test MA calculation
    double ma = CalculateMA(InpLookbackWindow);
    Print("📈 Moving Average (", InpLookbackWindow, " periods): ", DoubleToString(ma, _Digits));
    
    // Test signal generation
    double current_price = iClose(_Symbol, PERIOD_D1, 0);
    Print("💰 Current Price: ", DoubleToString(current_price, _Digits));
    
    string signal = GenerateSignal(current_price, ma);
    Print("🎯 Generated Signal: ", signal);
    
    // Show signal analysis
    Print("🔍 Signal Analysis:");
    Print("   Current Price: ", DoubleToString(current_price, _Digits));
    Print("   MA: ", DoubleToString(ma, _Digits));
    Print("   Threshold: ", DoubleToString(InpThreshold * 100, 2), "%");
    Print("   Buy Level: ", DoubleToString(ma * (1 - InpThreshold), _Digits));
    Print("   Sell Level: ", DoubleToString(ma * (1 + InpThreshold), _Digits));
    Print("   Price Deviation: ", DoubleToString(MathAbs(current_price - ma) / ma * 100, 2), "%");
    
    Print("");
    Print("✅ Data Test EA Aggressive initialized successfully");
    Print("🚀 TRADING IS ENABLED - Will execute trades when signals are generated!");
    Print("⚡ AGGRESSIVE MODE - Very sensitive to price movements!");
    g_initialized = true;
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 Data Test EA Aggressive deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    g_tickCount++;
    
    // Check every tick for maximum sensitivity
    if(g_tickCount % 1 == 0)
    {
        // Check if we should trade
        if(!ShouldTrade())
        {
            if(g_tickCount % 50 == 0) // Less frequent debug output
                Print("❌ ShouldTrade() returned false - skipping tick ", g_tickCount);
            return;
        }
        
        // Get current price
        double current_price = iClose(_Symbol, PERIOD_D1, 0);
        
        // Calculate MA
        double ma = CalculateMA(InpLookbackWindow);
        
        if(ma <= 0)
        {
            Print("❌ Invalid MA value: ", ma);
            return;
        }
        
        // Generate signal
        string signal = GenerateSignal(current_price, ma);
        
        // Show analysis every 50 ticks
        if(g_tickCount % 50 == 0)
        {
            Print("=== TICK ", g_tickCount, " ===");
            Print("💰 Current Price: ", DoubleToString(current_price, _Digits));
            Print("📈 Moving Average: ", DoubleToString(ma, _Digits));
            Print("🎯 Signal: ", signal);
            Print("🔍 Signal Analysis:");
            Print("   Current Price: ", DoubleToString(current_price, _Digits));
            Print("   MA: ", DoubleToString(ma, _Digits));
            Print("   Threshold: ", DoubleToString(InpThreshold * 100, 2), "%");
            Print("   Buy Level: ", DoubleToString(ma * (1 - InpThreshold), _Digits));
            Print("   Sell Level: ", DoubleToString(ma * (1 + InpThreshold), _Digits));
            Print("   Price Deviation: ", DoubleToString(MathAbs(current_price - ma) / ma * 100, 2), "%");
        }
        
        // Execute trades
        if(signal == "BUY")
        {
            Print("🟢 BUY Signal Generated - Opening Position");
            OpenPosition(ORDER_TYPE_BUY, current_price);
        }
        else if(signal == "SELL")
        {
            Print("🔴 SELL Signal Generated - Opening Position");
            OpenPosition(ORDER_TYPE_SELL, current_price);
        }
        else if(g_tickCount % 50 == 0)
        {
            Print("⚪ HOLD Signal - No action");
        }
    }
}

//+------------------------------------------------------------------+
//| Check if we should trade                                         |
//+------------------------------------------------------------------+
bool ShouldTrade()
{
    // Check if market is closed
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
    {
        return false;
    }
    
    // Check if we have open positions
    if(PositionsTotal() > 0)
    {
        return false;
    }
    
    // Check if enough time has passed since last trade (shorter interval for aggressive mode)
    if(TimeCurrent() - g_lastTradeTime < 30) // 30 seconds minimum between trades
    {
        return false;
    }
    
    return true;
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
//| Generate trading signal based on mean reversion strategy        |
//+------------------------------------------------------------------+
string GenerateSignal(double currentPrice, double ma)
{
    if(ma <= 0)
        return "NO_MA_DATA";
    
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
//| Open a new position                                             |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE orderType, double price)
{
    Print("🚀 Attempting to open position...");
    
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
    
    Print("🎯 Order Details:");
    Print("   Type: ", (orderType == ORDER_TYPE_BUY ? "BUY" : "SELL"));
    Print("   Price: ", DoubleToString(price, _Digits));
    Print("   Stop Loss: ", DoubleToString(sl, _Digits));
    Print("   Take Profit: ", DoubleToString(tp, _Digits));
    Print("   Volume: ", DoubleToString(InpPositionSize, 2));
    
    // Prepare trade request
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = _Symbol;
    request.volume = InpPositionSize;
    request.type = orderType;
    request.price = price;
    request.sl = sl;
    request.tp = tp;
    request.deviation = 20;
    request.magic = 234002;
    request.comment = "DataTestAggressive";
    request.type_filling = ORDER_FILLING_IOC;
    
    // Send order
    bool success = OrderSend(request, result);
    
    if(success && result.retcode == TRADE_RETCODE_DONE)
    {
        Print("✅ Position opened successfully!");
        Print("   Ticket: ", result.order);
        Print("   Volume: ", DoubleToString(InpPositionSize, 2));
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