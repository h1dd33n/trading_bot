#!/usr/bin/env python3
"""
Simple Live Trade Test using Prop Firm Bot connection method
"""

import MetaTrader5 as mt5
import structlog
import time

logger = structlog.get_logger()

def test_simple_trade():
    """Test a simple live trade using the same connection method as prop firm bot."""
    
    print("🧪 Simple Live Trade Test")
    print("=" * 40)
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return False
    
    # Login
    if not mt5.login(login="2194718", password="vUD&V86dwc", server="ACGMarkets-Main"):
        print("❌ MT5 login failed")
        mt5.shutdown()
        return False
    
    print("✅ Connected to MT5")
    
    # Get account info
    account_info = mt5.account_info()
    print(f"💰 Account Balance: ${account_info.balance:,.2f}")
    print(f"📈 Current Equity: ${account_info.equity:,.2f}")
    
    # Test symbol
    symbol = "EURAUD.pro"
    
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"❌ Could not get symbol info for {symbol}")
        mt5.shutdown()
        return False
    
    print(f"\n📊 Symbol: {symbol}")
    print(f"   Bid: {symbol_info.bid}")
    print(f"   Ask: {symbol_info.ask}")
    print(f"   Volume Min: {symbol_info.volume_min}")
    
    # Small position size
    volume = 0.01  # Minimum lot size
    current_price = (symbol_info.bid + symbol_info.ask) / 2
    
    print(f"\n📈 Current Price: {current_price:.5f}")
    print(f"📊 Position Size: {volume} lots")
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will place a REAL trade!")
    print(f"   Symbol: {symbol}")
    print(f"   Volume: {volume} lots")
    print(f"   Price: {current_price:.5f}")
    
    confirm = input("\nDo you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Test cancelled")
        mt5.shutdown()
        return False
    
    try:
        # Open BUY position
        print(f"\n🔄 Opening BUY position...")
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": symbol_info.ask,
            "deviation": 20,
            "magic": 234000,
            "comment": "simple_test",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Order failed: {result.retcode} - {result.comment}")
            mt5.shutdown()
            return False
        
        print(f"✅ BUY order placed!")
        print(f"   Ticket: {result.order}")
        print(f"   Price: {result.price}")
        
        # Wait and check position
        time.sleep(2)
        positions = mt5.positions_get(symbol=symbol)
        
        if positions and len(positions) > 0:
            position = positions[0]
            print(f"✅ Position opened!")
            print(f"   Ticket: {position.ticket}")
            print(f"   Profit: ${position.profit:.2f}")
            
            # Close position
            print(f"\n🔄 Closing position...")
            
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL,
                "position": position.ticket,
                "price": symbol_info.bid,
                "deviation": 20,
                "magic": 234000,
                "comment": "simple_test_close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            close_result = mt5.order_send(close_request)
            if close_result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position closed!")
                print(f"   Close Ticket: {close_result.order}")
                
                # Final account status
                final_account = mt5.account_info()
                profit = final_account.equity - account_info.equity
                print(f"\n📊 Final Profit: ${profit:.2f}")
                print(f"🎉 Test completed!")
                return True
            else:
                print(f"❌ Close failed: {close_result.retcode}")
                return False
        else:
            print("❌ No position found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    test_simple_trade() 