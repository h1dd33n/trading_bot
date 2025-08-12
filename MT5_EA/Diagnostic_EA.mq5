//+------------------------------------------------------------------+
//|                                            Diagnostic_EA.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Diagnostic EA - Checks MT5 settings"

//--- Global Variables
int g_tickCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    g_tickCount = 0;
    
    Print("=== MT5 DIAGNOSTIC REPORT ===");
    Print("");
    
    // Check basic trading permissions
    Print("🔍 TRADING PERMISSIONS:");
    Print("   MQL_TRADE_ALLOWED: ", (MQLInfoInteger(MQL_TRADE_ALLOWED) ? "✅ YES" : "❌ NO"));
    Print("   MQL_DLLS_ALLOWED: ", (MQLInfoInteger(MQL_DLLS_ALLOWED) ? "✅ YES" : "❌ NO"));
    Print("");
    
    // Check symbol information
    Print("🔍 SYMBOL INFORMATION:");
    Print("   Symbol: ", _Symbol);
    Print("   Symbol Trade Mode: ", SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE));
    Print("   Symbol Select: ", (SymbolSelect(_Symbol, true) ? "✅ YES" : "❌ NO"));
    Print("   Symbol Visible: ", (SymbolInfoInteger(_Symbol, SYMBOL_VISIBLE) ? "✅ YES" : "❌ NO"));
    Print("");
    
    // Check account information
    Print("🔍 ACCOUNT INFORMATION:");
    Print("   Account Type: ", AccountInfoInteger(ACCOUNT_TRADE_MODE));
    Print("   Account Currency: ", AccountInfoString(ACCOUNT_CURRENCY));
    Print("   Account Balance: ", AccountInfoDouble(ACCOUNT_BALANCE));
    Print("   Account Equity: ", AccountInfoDouble(ACCOUNT_EQUITY));
    Print("");
    
    // Check terminal information
    Print("🔍 TERMINAL INFORMATION:");
    Print("   Terminal Connected: ", (TerminalInfoInteger(TERMINAL_CONNECTED) ? "✅ YES" : "❌ NO"));
    Print("   Terminal Trade Allowed: ", (TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) ? "✅ YES" : "❌ NO"));
    Print("   Terminal Path: ", TerminalInfoString(TERMINAL_PATH));
    Print("");
    
    // Check data availability
    Print("🔍 DATA AVAILABILITY:");
    int bars_m1 = Bars(_Symbol, PERIOD_M1);
    int bars_m5 = Bars(_Symbol, PERIOD_M5);
    int bars_h1 = Bars(_Symbol, PERIOD_H1);
    Print("   M1 Bars: ", bars_m1);
    Print("   M5 Bars: ", bars_m5);
    Print("   H1 Bars: ", bars_h1);
    Print("");
    
    // Check current price
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    Print("🔍 CURRENT PRICES:");
    Print("   Bid: ", DoubleToString(bid, _Digits));
    Print("   Ask: ", DoubleToString(ask, _Digits));
    Print("   Spread: ", DoubleToString(ask - bid, _Digits));
    Print("");
    
    // Summary
    Print("🔍 DIAGNOSTIC SUMMARY:");
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
    {
        Print("❌ CRITICAL: Automated trading is NOT allowed!");
        Print("   → Go to Tools → Options → Expert Advisors");
        Print("   → Check 'Allow automated trading'");
        return INIT_FAILED;
    }
    
    if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
    {
        Print("❌ CRITICAL: Terminal trading is NOT allowed!");
        Print("   → Check your broker settings");
        return INIT_FAILED;
    }
    
    if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
    {
        Print("❌ CRITICAL: Symbol trading is NOT allowed!");
        Print("   → Try a different symbol (EURUSD)");
        return INIT_FAILED;
    }
    
    if(bars_m1 < 100)
    {
        Print("⚠️  WARNING: Limited M1 data available");
        Print("   → Try downloading more data");
    }
    
    Print("✅ All basic checks passed!");
    Print("✅ Ready for trading!");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 Diagnostic EA finished. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    g_tickCount++;
    
    // Show tick information every 100 ticks
    if(g_tickCount % 100 == 0)
    {
        Print("=== TICK ", g_tickCount, " ===");
        Print("   Time: ", TimeToString(TimeCurrent()));
        Print("   Bid: ", DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_BID), _Digits));
        Print("   Ask: ", DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_ASK), _Digits));
        Print("   Positions: ", PositionsTotal());
        Print("   Orders: ", OrdersTotal());
        Print("");
    }
} 