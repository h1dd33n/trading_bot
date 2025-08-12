#!/usr/bin/env python3
"""
Test Live Trade - Open and Close a Small Position
"""

import MetaTrader5 as mt5
import structlog
import time
from datetime import datetime

logger = structlog.get_logger()

def test_live_trade():
    """Test opening and closing a small position."""
    
    print("🧪 Testing Live Trade - Open and Close Position")
    print("=" * 60)
    
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
    
    print(f"\n📊 Symbol Info for {symbol}:")
    print(f"   Bid: {symbol_info.bid}")
    print(f"   Ask: {symbol_info.ask}")
    print(f"   Point: {symbol_info.point}")
    print(f"   Digits: {symbol_info.digits}")
    print(f"   Volume Min: {symbol_info.volume_min}")
    print(f"   Volume Max: {symbol_info.volume_max}")
    print(f"   Volume Step: {symbol_info.volume_step}")
    
    # Calculate small position size (0.01 lots = $1,000 worth)
    volume = 0.01  # Minimum lot size
    current_price = (symbol_info.bid + symbol_info.ask) / 2
    
    print(f"\n📈 Current Price: {current_price:.5f}")
    print(f"📊 Position Size: {volume} lots")
    print(f"💰 Position Value: ${volume * current_price * 100000:,.2f}")
    
    # Calculate stop loss and take profit (very tight for testing)
    sl = current_price * 0.999  # 0.1% stop loss
    tp = current_price * 1.001  # 0.1% take profit
    
    print(f"🛑 Stop Loss: {sl:.5f}")
    print(f"🎯 Take Profit: {tp:.5f}")
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will place a REAL trade!")
    print(f"   Symbol: {symbol}")
    print(f"   Volume: {volume} lots")
    print(f"   Price: {current_price:.5f}")
    print(f"   Stop Loss: {sl:.5f}")
    print(f"   Take Profit: {tp:.5f}")
    
    confirm = input("\nDo you want to proceed with this test trade? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Test cancelled by user")
        mt5.shutdown()
        return False
    
    try:
        # Step 1: Open BUY position
        print(f"\n🔄 Opening BUY position...")
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": symbol_info.ask,  # Use ask price for buy
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": "test_live_trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Order failed: {result.retcode} - {result.comment}")
            mt5.shutdown()
            return False
        
        print(f"✅ BUY order placed successfully!")
        print(f"   Order Ticket: {result.order}")
        print(f"   Volume: {result.volume}")
        print(f"   Price: {result.price}")
        
        # Wait a moment for the order to be processed
        time.sleep(2)
        
        # Step 2: Check if position was opened
        print(f"\n🔍 Checking for open position...")
        positions = mt5.positions_get(symbol=symbol)
        
        if positions is None or len(positions) == 0:
            print("❌ No position found - order may not have been filled")
            mt5.shutdown()
            return False
        
        position = positions[0]
        print(f"✅ Position found!")
        print(f"   Ticket: {position.ticket}")
        print(f"   Symbol: {position.symbol}")
        print(f"   Type: {'BUY' if position.type == mt5.POSITION_TYPE_BUY else 'SELL'}")
        print(f"   Volume: {position.volume}")
        print(f"   Price Open: {position.price_open}")
        print(f"   Price Current: {position.price_current}")
        print(f"   Profit: ${position.profit:.2f}")
        print(f"   Stop Loss: {position.sl}")
        print(f"   Take Profit: {position.tp}")
        
        # Step 3: Close the position
        print(f"\n🔄 Closing position...")
        
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL,  # Sell to close BUY position
            "position": position.ticket,
            "price": symbol_info.bid,  # Use bid price for sell
            "deviation": 20,
            "magic": 234000,
            "comment": "test_live_trade_close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        close_result = mt5.order_send(close_request)
        if close_result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Close order failed: {close_result.retcode} - {close_result.comment}")
            mt5.shutdown()
            return False
        
        print(f"✅ Position closed successfully!")
        print(f"   Close Ticket: {close_result.order}")
        print(f"   Close Price: {close_result.price}")
        
        # Wait a moment for the close to be processed
        time.sleep(2)
        
        # Step 4: Verify position is closed
        print(f"\n🔍 Verifying position is closed...")
        positions_after = mt5.positions_get(symbol=symbol)
        
        if positions_after is None or len(positions_after) == 0:
            print("✅ Position successfully closed!")
        else:
            print("❌ Position still open - close may have failed")
            for pos in positions_after:
                print(f"   Remaining position: {pos.ticket} - {pos.volume} lots")
        
        # Step 5: Show final account status
        print(f"\n📊 Final Account Status:")
        final_account = mt5.account_info()
        print(f"   Balance: ${final_account.balance:,.2f}")
        print(f"   Equity: ${final_account.equity:,.2f}")
        print(f"   Profit: ${final_account.equity - account_info.equity:,.2f}")
        
        print(f"\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    test_live_trade() 