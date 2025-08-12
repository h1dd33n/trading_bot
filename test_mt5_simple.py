#!/usr/bin/env python3
"""
Simple MT5 Connection Test
"""

import MetaTrader5 as mt5

def test_simple_connection():
    """Test basic MT5 connection without login."""
    
    print("🔍 Simple MT5 Connection Test")
    print("=" * 40)
    
    # Step 1: Initialize without login
    print("1. Initializing MT5...")
    if not mt5.initialize():
        error = mt5.last_error()
        print(f"   ❌ Initialization failed: {error}")
        return
    else:
        print("   ✅ MT5 initialized successfully")
    
    # Step 2: Get terminal info
    print("\n2. Getting terminal info...")
    terminal_info = mt5.terminal_info()
    if terminal_info is not None:
        print(f"   Terminal: {terminal_info.name}")
        print(f"   Version: {terminal_info.version}")
        print(f"   Connected: {terminal_info.connected}")
        print(f"   Trade allowed: {terminal_info.trade_allowed}")
        print(f"   Expert advisors allowed: {not terminal_info.tradeapi_disabled}")
    else:
        print("   ❌ Could not get terminal info")
    
    # Step 3: Check if already logged in
    print("\n3. Checking if already logged in...")
    account_info = mt5.account_info()
    if account_info is not None:
        print(f"   ✅ Already logged in!")
        print(f"   Account: {account_info.login}")
        print(f"   Server: {account_info.server}")
        print(f"   Balance: {account_info.balance}")
        print(f"   Trade allowed: {account_info.trade_allowed}")
    else:
        print("   ⚠️  Not logged in - this is normal")
    
    # Step 4: Try to login
    print("\n4. Attempting login...")
    login = "2194718"
    password = "vUD&V86dwc"
    server = "ACGMarkets-Main"
    
    if not mt5.login(login=login, password=password, server=server):
        error = mt5.last_error()
        print(f"   ❌ Login failed: {error}")
        
        # Additional troubleshooting info
        print("\n   🔧 Troubleshooting steps:")
        print("   1. Open MT5 terminal manually")
        print("   2. Log in with the same credentials")
        print("   3. Go to Tools → Options → Expert Advisors")
        print("   4. Enable 'Allow automated trading'")
        print("   5. Enable 'Allow DLL imports'")
        print("   6. Restart MT5 terminal")
        print("   7. Try this test again")
        
    else:
        print("   ✅ Login successful!")
        account_info = mt5.account_info()
        if account_info:
            print(f"   Account: {account_info.login}")
            print(f"   Server: {account_info.server}")
            print(f"   Balance: {account_info.balance}")
    
    # Cleanup
    mt5.shutdown()
    print("\n✅ Test completed")

if __name__ == "__main__":
    test_simple_connection() 