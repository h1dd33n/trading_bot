#!/usr/bin/env python3
"""
Test MT5 Data Structure
"""

import MetaTrader5 as mt5
import pandas as pd
import structlog

logger = structlog.get_logger()

def test_mt5_data_structure():
    """Test MT5 data structure to understand the column names."""
    
    print("🔍 Testing MT5 Data Structure")
    print("=" * 40)
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return
    
    # Login
    if not mt5.login(login="2194718", password="vUD&V86dwc", server="ACGMarkets-Main"):
        print("❌ MT5 login failed")
        mt5.shutdown()
        return
    
    print("✅ Connected to MT5")
    
    # Test symbol
    symbol = "EURAUD.pro"
    
    # Get rates
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 5)
    
    if rates is None:
        print(f"❌ No data received for {symbol}")
    else:
        print(f"✅ Received {len(rates)} data points for {symbol}")
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        print(f"\n📊 DataFrame columns: {df.columns.tolist()}")
        print(f"📊 DataFrame shape: {df.shape}")
        
        # Show first row
        print(f"\n📈 First row data:")
        for col in df.columns:
            print(f"   {col}: {df[col].iloc[0]}")
        
        # Check if 'close' column exists
        if 'close' in df.columns:
            print(f"\n✅ 'close' column found")
            print(f"   Sample values: {df['close'].head().tolist()}")
        else:
            print(f"\n❌ 'close' column not found")
            print(f"   Available columns: {df.columns.tolist()}")
    
    # Cleanup
    mt5.shutdown()
    print("\n✅ Test completed")

if __name__ == "__main__":
    test_mt5_data_structure() 