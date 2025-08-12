//+------------------------------------------------------------------+
//|                                           test_data_availability.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Test Data Availability and MA Calculation"

//--- Input Parameters
input int      InpLookbackWindow = 30;        // Lookback window for MA calculation
input double   InpThreshold = 0.01;           // Threshold for signal generation (1%)

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== Data Availability Test ===");
    Print("Symbol: ", _Symbol);
    Print("Period: ", EnumToString(Period()));
    Print("Lookback Window: ", InpLookbackWindow);
    Print("Threshold: ", InpThreshold);
    Print("");
    
    // Test data availability
    int total_bars = Bars(_Symbol, PERIOD_D1);
    Print("Total bars available: ", total_bars);
    
    if(total_bars < InpLookbackWindow)
    {
        Print("❌ ERROR: Insufficient data! Need at least ", InpLookbackWindow, " bars, but only have ", total_bars);
        return;
    }
    
    // Test MA calculation
    double ma = CalculateMA(InpLookbackWindow);
    Print("Moving Average (", InpLookbackWindow, " periods): ", DoubleToString(ma, _Digits));
    
    // Test signal generation
    double current_price = iClose(_Symbol, PERIOD_D1, 0);
    Print("Current Price: ", DoubleToString(current_price, _Digits));
    
    string signal = GenerateSignal(current_price, ma);
    Print("Generated Signal: ", signal);
    
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
    Print("=== Test Complete ===");
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