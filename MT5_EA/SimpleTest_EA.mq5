//+------------------------------------------------------------------+
//|                                              SimpleTest_EA.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Simple Test EA - Will trade on every tick"

//--- Input Parameters
input double   InpPositionSize = 0.01;        // Position size in lots
input int      InpMaxTrades = 10;             // Maximum number of trades to make

//--- Global Variables
int g_tradeCount = 0;
bool g_initialized = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    g_tradeCount = 0;
    g_initialized = false;
    
    Print("=== Simple Test EA ===");
    Print("Symbol: ", _Symbol);
    Print("Period: ", EnumToString(Period()));
    Print("Position Size: ", InpPositionSize, " lots");
    Print("Max Trades: ", InpMaxTrades);
    Print("");
    
    // Check if trading is allowed
    if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
    {
        Print("❌ ERROR: Automated trading is NOT allowed!");
        Print("   Go to Tools → Options → Expert Advisors");
        Print("   Check 'Allow automated trading'");
        return INIT_FAILED;
    }
    
    // Check if symbol is available
    if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
    {
        Print("❌ ERROR: Trading is not allowed for symbol: ", _Symbol);
        return INIT_FAILED;
    }
    
    Print("✅ Simple Test EA initialized successfully");
    Print("🚀 Will trade on every tick until max trades reached!");
    g_initialized = true;
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🔚 Simple Test EA deinitialized. Reason: ", reason);
    Print("📊 Total trades made: ", g_tradeCount);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if we should trade
    if(!ShouldTrade())
    {
        return;
    }
    
    // Get current price
    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    
    // Alternate between BUY and SELL
    ENUM_ORDER_TYPE orderType = (g_tradeCount % 2 == 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    
    Print("🔄 TICK ", g_tradeCount + 1, " - Opening ", (orderType == ORDER_TYPE_BUY ? "BUY" : "SELL"), " position");
    
    // Open position
    OpenPosition(orderType, current_price);
    
    g_tradeCount++;
}

//+------------------------------------------------------------------+
//| Check if we should trade                                         |
//+------------------------------------------------------------------+
bool ShouldTrade()
{
    // Check if we've reached max trades
    if(g_tradeCount >= InpMaxTrades)
    {
        return false;
    }
    
    // Check if we have open positions (don't open new ones)
    if(PositionsTotal() > 0)
    {
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Open a new position                                             |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE orderType, double price)
{
    Print("🚀 Opening position...");
    
    // Prepare trade request
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = _Symbol;
    request.volume = InpPositionSize;
    request.type = orderType;
    request.price = price;
    request.deviation = 20;
    request.magic = 999999;
    request.comment = "SimpleTest";
    request.type_filling = ORDER_FILLING_IOC;
    
    // Send order
    bool success = OrderSend(request, result);
    
    if(success && result.retcode == TRADE_RETCODE_DONE)
    {
        Print("✅ Position opened successfully!");
        Print("   Ticket: ", result.order);
        Print("   Type: ", (orderType == ORDER_TYPE_BUY ? "BUY" : "SELL"));
        Print("   Volume: ", DoubleToString(InpPositionSize, 2));
        Print("   Price: ", DoubleToString(price, _Digits));
    }
    else
    {
        Print("❌ Failed to open position!");
        Print("   Error Code: ", result.retcode);
        Print("   Error Comment: ", result.comment);
    }
} 