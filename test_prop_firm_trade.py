#!/usr/bin/env python3
"""
Test Prop Firm Bot Trade - Using the bot's own connection method
"""

import asyncio
import MetaTrader5 as mt5
from prop_firm_bot import PropFirmBot, PropFirmConfig

async def test_prop_firm_trade():
    """Test a small trade using the prop firm bot's connection method."""
    
    print("🧪 Testing Prop Firm Bot Trade")
    print("=" * 50)
    
    # Create bot with test configuration
    config = PropFirmConfig()
    config.position_size_pct = 0.0001  # Very small position (0.01% of capital)
    config.stop_loss_pct = 0.001  # Very tight stop loss (0.1%)
    config.take_profit_pct = 0.001  # Very tight take profit (0.1%)
    
    bot = PropFirmBot(config)
    
    # Connect to MT5
    if not bot.connect_mt5():
        print("❌ Failed to connect to MT5")
        return False
    
    print("✅ Connected to MT5")
    
    # Get account info
    account_info = mt5.account_info()
    print(f"💰 Account Balance: ${account_info.balance:,.2f}")
    print(f"📈 Current Equity: ${account_info.equity:,.2f}")
    
    # Test symbol
    symbol = "EURAUD.pro"
    
    # Get symbol info
    symbol_info = bot.get_symbol_info(symbol)
    if symbol_info is None:
        print(f"❌ Could not get symbol info for {symbol}")
        bot.disconnect_mt5()
        return False
    
    print(f"\n📊 Symbol: {symbol}")
    print(f"   Bid: {symbol_info['bid']}")
    print(f"   Ask: {symbol_info['ask']}")
    print(f"   Volume Min: {symbol_info['volume_min']}")
    
    # Get current price
    current_price = bot.get_current_price(symbol)
    if current_price is None:
        print(f"❌ Could not get current price for {symbol}")
        bot.disconnect_mt5()
        return False
    
    print(f"\n📈 Current Price: {current_price:.5f}")
    
    # Calculate position size
    base_position_size = account_info.equity * config.position_size_pct
    volume = base_position_size / current_price
    volume = round(volume / symbol_info['volume_step']) * symbol_info['volume_step']
    volume = max(volume, symbol_info['volume_min'])
    
    print(f"📊 Position Size: {volume} lots")
    print(f"💰 Position Value: ${volume * current_price * 100000:,.2f}")
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will place a REAL trade!")
    print(f"   Symbol: {symbol}")
    print(f"   Volume: {volume} lots")
    print(f"   Price: {current_price:.5f}")
    
    confirm = input("\nDo you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Test cancelled")
        bot.disconnect_mt5()
        return False
    
    try:
        # Calculate stop loss and take profit
        sl = current_price * (1 - config.stop_loss_pct)
        tp = current_price * (1 + config.take_profit_pct)
        
        print(f"\n🔄 Opening BUY position...")
        print(f"   Stop Loss: {sl:.5f}")
        print(f"   Take Profit: {tp:.5f}")
        
        # Place order using bot's method
        order_ticket = bot.place_order(symbol, "BUY", volume, current_price, sl, tp)
        
        if order_ticket is None:
            print("❌ Order failed")
            bot.disconnect_mt5()
            return False
        
        print(f"✅ BUY order placed!")
        print(f"   Ticket: {order_ticket}")
        
        # Wait and check position
        await asyncio.sleep(2)
        positions = bot.get_positions()
        
        if positions:
            position = positions[0]
            print(f"✅ Position opened!")
            print(f"   Ticket: {position['ticket']}")
            print(f"   Profit: ${position['profit']:.2f}")
            
            # Close position
            print(f"\n🔄 Closing position...")
            
            close_ticket = bot.place_order(symbol, "SELL", position['volume'], current_price, 0, 0)
            
            if close_ticket:
                print(f"✅ Position closed!")
                print(f"   Close Ticket: {close_ticket}")
                
                # Final account status
                final_account = mt5.account_info()
                profit = final_account.equity - account_info.equity
                print(f"\n📊 Final Profit: ${profit:.2f}")
                print(f"🎉 Test completed!")
                return True
            else:
                print("❌ Close failed")
                return False
        else:
            print("❌ No position found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        bot.disconnect_mt5()

if __name__ == "__main__":
    asyncio.run(test_prop_firm_trade()) 