#!/usr/bin/env python3
"""
Debug script to test RSI calculation and data structure.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from test_config import setup_test_environment
from data.data_manager import get_data_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_rsi_calculation():
    """Debug RSI calculation and data structure."""
    print("Debugging RSI calculation...")
    
    try:
        data_manager = await get_data_manager()
        
        # Use very recent dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Just 7 days for testing
        
        print(f"Fetching data from {start_date.date()} to {end_date.date()}")
        
        # Test fetching data for AAPL
        data = await data_manager.fetch_historical_data(
            "AAPL", 
            period="1wk", 
            interval="1h",
            start_date=start_date,
            end_date=end_date
        )
        
        if not data.empty:
            print(f"✅ Successfully fetched {len(data)} records for AAPL")
            print(f"   Columns: {data.columns.tolist()}")
            print(f"   Date range: {data.index.min()} to {data.index.max()}")
            
            # Test indicator calculation
            data_with_indicators = await data_manager.calculate_indicators(data, "AAPL")
            print(f"✅ Successfully calculated indicators")
            print(f"   All columns: {data_with_indicators.columns.tolist()}")
            
            # Check RSI specifically
            if 'rsi' in data_with_indicators.columns:
                rsi_values = data_with_indicators['rsi'].dropna()
                print(f"   RSI values: {len(rsi_values)} non-null values")
                if len(rsi_values) > 0:
                    print(f"   RSI range: {rsi_values.min():.2f} to {rsi_values.max():.2f}")
                    print(f"   Latest RSI: {rsi_values.iloc[-1]:.2f}")
                else:
                    print("   ⚠️ No valid RSI values found")
            else:
                print("   ❌ RSI column not found!")
            
            # Check other indicators
            indicator_columns = ['moving_avg', 'std_dev', 'z_score', 'rsi', 'bollinger_upper', 'bollinger_lower', 'bollinger_middle']
            for col in indicator_columns:
                if col in data_with_indicators.columns:
                    non_null_count = data_with_indicators[col].notna().sum()
                    print(f"   {col}: {non_null_count} non-null values")
                else:
                    print(f"   ❌ {col} column missing!")
            
        else:
            print("❌ No data fetched for AAPL")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the debug test."""
    print("🐛 Debugging RSI Calculation")
    print("=" * 50)
    
    # Set up test environment
    setup_test_environment()
    
    try:
        await debug_rsi_calculation()
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 