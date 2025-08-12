#!/usr/bin/env python3
"""
Simple MT5 Data Test using Prop Firm Bot connection
"""

import MetaTrader5 as mt5
import pandas as pd
import structlog

logger = structlog.get_logger()

def test_data():
    """Test MT5 data using the same connection method as prop firm bot."""
    
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
    
    try:
        # Get rates
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 5)
        
        if rates is None or len(rates) == 0:
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
                
                # Test the rename operation
                df_renamed = df.rename(columns={'close': 'Close'})
                print(f"\n✅ After rename - 'Close' column: {df_renamed['Close'].head().tolist()}")
            else:
                print(f"\n❌ 'close' column not found")
                print(f"   Available columns: {df.columns.tolist()}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Cleanup
    mt5.shutdown()
    print("\n✅ Test completed")

if __name__ == "__main__":
    test_data() 