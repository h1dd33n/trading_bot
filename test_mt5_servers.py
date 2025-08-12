#!/usr/bin/env python3
"""
Test MT5 connection with different server variations
"""

import MetaTrader5 as mt5

def test_server_variations():
    """Test connection with different server name variations."""
    
    print("🔍 Testing MT5 Server Variations")
    print("=" * 50)
    
    # Server name variations to try
    server_variations = [
        "ACGMarkets-Main",
        "ACGMarkets",
        "ACG-Main", 
        "ACG",
        "ACGMarkets-Demo",
        "ACGMarkets-Live"
    ]
    
    login = "2194718"
    password = "vUD&V86dwc"
    
    for server in server_variations:
        print(f"\n🔄 Testing server: {server}")
        
        # Initialize MT5
        if not mt5.initialize():
            error = mt5.last_error()
            print(f"   ❌ Initialization failed: {error}")
            mt5.shutdown()
            continue
        
        # Try to login
        if mt5.login(login=login, password=password, server=server):
            print(f"   ✅ SUCCESS! Connected to {server}")
            account_info = mt5.account_info()
            if account_info:
                print(f"   Account: {account_info.login}")
                print(f"   Server: {account_info.server}")
                print(f"   Balance: {account_info.balance}")
                print(f"   Trade allowed: {account_info.trade_allowed}")
            
            mt5.shutdown()
            return server
        else:
            error = mt5.last_error()
            print(f"   ❌ Login failed: {error}")
            mt5.shutdown()
    
    print("\n❌ None of the server variations worked.")
    print("\n🔧 Please check:")
    print("1. Open MT5 terminal manually")
    print("2. Log in and check the exact server name")
    print("3. Go to Tools → Options → Expert Advisors")
    print("4. Enable 'Allow automated trading'")
    print("5. Restart MT5 terminal")
    
    return None

if __name__ == "__main__":
    test_server_variations() 