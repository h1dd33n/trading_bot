//+------------------------------------------------------------------+
//|                                                DataTest_EA.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Data Availability Test EA"

//--- Input Parameters
input int      InpLookbackWindow = 30;        // Lookback window for MA calculation
input double   InpThreshold = 0.01;           // Threshold for signal generation (1%)
input bool     InpEnableTrading = false;      // Enable actual trading (false for testing only)

//--- Global Variables
int g_tickCount = 0;
bool g_initialized = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    g_tickCount = 0;
    g_initialized = false;
    
    Print("=== Data Availability Test EA ===");
    Print("Symbol: ", _Symbol);
    Print("Period: ", EnumToString(Period()));
    Print("Lookback Window: ", InpLookbackWindow);
    Print("Threshold: ", InpThreshold);
    Print("Trading Enabled: ", (InpEnableTrading ? "YES" : "NO"));
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
    
    // Test multiple periods
    Print("");
    Print("=== Testing Multiple Periods ===");
    for(int i = 0; i < 10; i++)
    {
        double price = iClose(_Symbol, PERIOD_D1, i);
        double ma_test = CalculateMA(InpLookbackWindow);
        string signal_test = GenerateSignal(price, ma_test);
        
        Print("Period ", i, ": Price=", DoubleToString(price, _Digits), 
              " MA=", DoubleToString(ma_test, _Digits), " Signal=", signal_test);
    }
    
    Print("");
    Print("✅ Data Test EA initialized successfully");
    g_initialized = true;
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 Data Test EA deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    g_tickCount++;
    
    // Only run test every 100 ticks to avoid spam
    if(g_tickCount % 100 == 0)
    {
        Print("=== TICK ", g_tickCount, " ===");
        
        // Get current price
        double current_price = iClose(_Symbol, PERIOD_D1, 0);
        Print("💰 Current Price: ", DoubleToString(current_price, _Digits));
        
        // Calculate MA
        double ma = CalculateMA(InpLookbackWindow);
        Print("📈 Moving Average: ", DoubleToString(ma, _Digits));
        
        // Generate signal
        string signal = GenerateSignal(current_price, ma);
        Print("🎯 Signal: ", signal);
        
        // Show signal analysis
        Print("🔍 Signal Analysis:");
        Print("   Current Price: ", DoubleToString(current_price, _Digits));
        Print("   MA: ", DoubleToString(ma, _Digits));
        Print("   Threshold: ", DoubleToString(InpThreshold * 100, 1), "%");
        Print("   Buy Level: ", DoubleToString(ma * (1 - InpThreshold), _Digits));
        Print("   Sell Level: ", DoubleToString(ma * (1 + InpThreshold), _Digits));
        
        // Check if we should trade
        if(signal == "BUY" || signal == "SELL")
        {
            Print("🟢 TRADING SIGNAL DETECTED: ", signal);
            
            if(InpEnableTrading)
            {
                Print("🚀 Trading is enabled - would open position");
                // Add trading logic here if needed
            }
            else
            {
                Print("⚠️  Trading is disabled - signal ignored");
            }
        }
        else
        {
            Print("⚪ No trading signal - HOLD");
        }
        
        Print("");
    }
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