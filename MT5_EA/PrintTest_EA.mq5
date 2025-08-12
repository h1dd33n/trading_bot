//+------------------------------------------------------------------+
//|                                              PrintTest_EA.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Simple Print Test EA"

//--- Global Variables
int g_tickCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== PRINT TEST EA STARTED ===");
    Print("Symbol: ", _Symbol);
    Print("Period: ", EnumToString(Period()));
    Print("Time: ", TimeToString(TimeCurrent()));
    Print("EA is running!");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== PRINT TEST EA STOPPED ===");
    Print("Reason: ", reason);
    Print("Total ticks processed: ", g_tickCount);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    g_tickCount++;
    
    // Print every 10 ticks
    if(g_tickCount % 10 == 0)
    {
        Print("TICK ", g_tickCount, " - Time: ", TimeToString(TimeCurrent()));
    }
} 