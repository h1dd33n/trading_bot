#!/usr/bin/env python3
"""
Simple test script to verify the fixes work properly.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from test_config import setup_test_environment
from data.data_manager import get_data_manager
from strategies.strategy_manager import get_strategy_manager
from risk.risk_manager import get_risk_manager
from backtesting.backtest_engine import get_backtest_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_fetching():
    """Test data fetching and storage."""
    print("Testing data fetching...")
    
    try:
        data_manager = await get_data_manager()
        
        # Test fetching data for AAPL with recent dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = await data_manager.fetch_historical_data(
            "AAPL", 
            period="1mo", 
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
            print(f"   Indicator columns: {[col for col in data_with_indicators.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]}")
            
        else:
            print("❌ No data fetched for AAPL")
            
    except Exception as e:
        print(f"❌ Error in data fetching: {e}")
        raise

async def test_backtest():
    """Test backtesting functionality."""
    print("\nTesting backtesting...")
    
    try:
        engine = await get_backtest_engine()
        
        # Run a simple backtest with recent dates
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        results = await engine.run_backtest(
            symbols=["AAPL"],
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0
        )
        
        if results:
            print(f"✅ Backtest completed successfully")
            print(f"   Total return: {results.total_return_pct:.2%}")
            print(f"   Sharpe ratio: {results.sharpe_ratio:.2f}")
            print(f"   Total trades: {results.total_trades}")
        else:
            print("❌ Backtest failed")
            
    except Exception as e:
        print(f"❌ Error in backtesting: {e}")
        raise

async def main():
    """Run all tests."""
    print("🧪 Testing Trading Bot Fixes")
    print("=" * 50)
    
    # Set up test environment
    setup_test_environment()
    
    try:
        await test_data_fetching()
        await test_backtest()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 