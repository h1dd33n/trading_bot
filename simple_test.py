#!/usr/bin/env python3
"""
Simple test script using very recent data to ensure yfinance returns results.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from test_config import setup_test_environment
from data.data_manager import get_data_manager
from backtesting.backtest_engine import get_backtest_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_recent_data():
    """Test with very recent data to ensure yfinance returns results."""
    print("Testing with recent data...")
    
    try:
        data_manager = await get_data_manager()
        
        # Use very recent dates (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"Fetching data from {start_date.date()} to {end_date.date()}")
        
        # Test fetching data for AAPL
        data = await data_manager.fetch_historical_data(
            "AAPL", 
            period="1mo", 
            interval="1h",
            start_date=start_date,
            end_date=end_date
        )
        
        if not data.empty:
            print(f"✅ Successfully fetched {len(data)} records for AAPL")
            print(f"   Date range: {data.index.min().date()} to {data.index.max().date()}")
            
            # Test backtest with this data
            engine = await get_backtest_engine()
            
            results = await engine.run_backtest(
                symbols=["AAPL"],
                start_date=start_date,
                end_date=end_date,
                initial_capital=100000.0
            )
            
            if results:
                print(f"✅ Backtest completed successfully")
                print(f"   Total return: {results.total_return_pct:.2%}")
                print(f"   Total trades: {results.total_trades}")
            else:
                print("❌ Backtest failed")
        else:
            print("❌ No data fetched for AAPL")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

async def main():
    """Run the simple test."""
    print("🧪 Simple Test with Recent Data")
    print("=" * 50)
    
    # Set up test environment
    setup_test_environment()
    
    try:
        await test_recent_data()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 