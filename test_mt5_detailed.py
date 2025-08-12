#!/usr/bin/env python3
"""
Detailed MT5 Connection Test
"""

import MetaTrader5 as mt5
import structlog

logger = structlog.get_logger()

def test_mt5_connection():
    """Test MT5 connection with detailed error reporting."""
    
    print("🔍 Detailed MT5 Connection Test")
    print("=" * 50)
    
    # Test 1: Check if MT5 module is available
    print("1. Checking MT5 module availability...")
    try:
        print(f"   MT5 version: {mt5.__version__}")
        print("   ✅ MT5 module is available")
    except Exception as e:
        print(f"   ❌ MT5 module error: {e}")
        return
    
    # Test 2: Initialize MT5
    print("\n2. Initializing MT5...")
    if not mt5.initialize():
        error = mt5.last_error()
        print(f"   ❌ MT5 initialization failed: {error}")
        print(f"   Error code: {error[0]}")
        print(f"   Error message: {error[1]}")
        
        # Common error codes and solutions
        if error[0] == -6:
            print("\n   💡 Error -6 (Authorization failed) solutions:")
            print("   - Make sure MT5 terminal is running")
            print("   - Check if you can log in manually to MT5")
            print("   - Verify credentials are correct")
            print("   - Try restarting MT5 terminal")
        elif error[0] == -1:
            print("\n   💡 Error -1 (No connection) solutions:")
            print("   - Check internet connection")
            print("   - Check if MT5 terminal is running")
        elif error[0] == -2:
            print("\n   💡 Error -2 (Invalid parameters) solutions:")
            print("   - Check login, password, and server parameters")
        
        return
    else:
        print("   ✅ MT5 initialized successfully")
    
    # Test 3: Get terminal info
    print("\n3. Getting terminal info...")
    terminal_info = mt5.terminal_info()
    if terminal_info is not None:
        print(f"   Terminal name: {terminal_info.name}")
        print(f"   Terminal path: {terminal_info.path}")
        print(f"   Terminal version: {terminal_info.version}")
        print(f"   Connected: {terminal_info.connected}")
        print(f"   Trade allowed: {terminal_info.trade_allowed}")
        print(f"   Expert advisors allowed: {terminal_info.tradeapi_disabled}")
    else:
        print("   ❌ Could not get terminal info")
    
    # Test 4: Try to login
    print("\n4. Testing login...")
    login = "2194718"
    password = "vUD&V86dwc"
    server = "ACGMarkets-Main"
    
    print(f"   Login: {login}")
    print(f"   Server: {server}")
    print(f"   Password: {'*' * len(password)}")
    
    if not mt5.login(login=login, password=password, server=server):
        error = mt5.last_error()
        print(f"   ❌ MT5 login failed: {error}")
        print(f"   Error code: {error[0]}")
        print(f"   Error message: {error[1]}")
        
        # Common login error codes
        if error[0] == -6:
            print("\n   💡 Login Error -6 solutions:")
            print("   - Verify login credentials in MT5 terminal")
            print("   - Check if account is active")
            print("   - Try logging in manually to MT5 first")
            print("   - Check if server name is correct")
        elif error[0] == -1:
            print("\n   💡 Login Error -1 solutions:")
            print("   - Check internet connection")
            print("   - Check if MT5 terminal is running")
        elif error[0] == -2:
            print("\n   💡 Login Error -2 solutions:")
            print("   - Check login, password, and server parameters")
        
        return
    else:
        print("   ✅ MT5 login successful")
    
    # Test 5: Get account info
    print("\n5. Getting account info...")
    account_info = mt5.account_info()
    if account_info is not None:
        print(f"   Account: {account_info.login}")
        print(f"   Server: {account_info.server}")
        print(f"   Balance: {account_info.balance}")
        print(f"   Equity: {account_info.equity}")
        print(f"   Margin: {account_info.margin}")
        print(f"   Free margin: {account_info.margin_free}")
        print(f"   Leverage: {account_info.leverage}")
        print(f"   Currency: {account_info.currency}")
        print(f"   Trade mode: {account_info.trade_mode}")
        print(f"   Trade allowed: {account_info.trade_allowed}")
    else:
        print("   ❌ Could not get account info")
    
    # Test 6: Get available symbols
    print("\n6. Getting available symbols...")
    symbols = mt5.symbols_get()
    if symbols is not None:
        print(f"   Total symbols available: {len(symbols)}")
        
        # Look for our target symbols
        target_symbols = ["EURAUD.pro", "EURCAD.pro", "EURAUD", "EURCAD"]
        found_symbols = []
        
        for symbol in symbols:
            if symbol.name in target_symbols:
                found_symbols.append(symbol.name)
                print(f"   ✅ Found symbol: {symbol.name}")
                print(f"      Trade mode: {symbol.trade_mode}")
                print(f"      Trade stops level: {symbol.trade_stops_level}")
                print(f"      Trade freeze level: {symbol.trade_freeze_level}")
        
        if not found_symbols:
            print("   ⚠️  Target symbols not found. Available symbols:")
            for i, symbol in enumerate(symbols[:10]):  # Show first 10
                print(f"      {symbol.name}")
            if len(symbols) > 10:
                print(f"      ... and {len(symbols) - 10} more")
    else:
        print("   ❌ Could not get symbols")
    
    # Cleanup
    mt5.shutdown()
    print("\n✅ MT5 connection test completed")

if __name__ == "__main__":
    test_mt5_connection() 