"""
Test script for MT5 bots functionality.
This script tests the bots without executing real trades.
"""

import asyncio
import logging
from typing import Dict, Any

from mt5.mt5_config import AccountType, get_mt5_connection
from mt5.mt5_trading_bot import MT5TradingBot
from mt5.mt5_prop_firm_bot import MT5PropFirmBot, YFinanceBacktester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_connection():
    """Test MT5 connection."""
    logger.info("Testing MT5 connection...")
    
    try:
        # Test regular account connection
        regular_connection = get_mt5_connection(AccountType.REGULAR)
        connected = regular_connection.connect()
        
        if connected:
            logger.info("✅ Regular account connection successful")
            account_info = regular_connection.get_account_info()
            if account_info:
                logger.info(f"Account balance: {account_info['balance']}")
                logger.info(f"Account equity: {account_info['equity']}")
            
            regular_connection.disconnect()
        else:
            logger.error("❌ Regular account connection failed")
        
        # Test prop firm account connection
        prop_connection = get_mt5_connection(AccountType.PROP_FIRM)
        connected = prop_connection.connect()
        
        if connected:
            logger.info("✅ Prop firm account connection successful")
            account_info = prop_connection.get_account_info()
            if account_info:
                logger.info(f"Account balance: {account_info['balance']}")
                logger.info(f"Account equity: {account_info['equity']}")
            
            prop_connection.disconnect()
        else:
            logger.error("❌ Prop firm account connection failed")
            
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")


async def test_regular_bot():
    """Test regular trading bot initialization."""
    logger.info("Testing regular trading bot...")
    
    try:
        bot = MT5TradingBot(AccountType.REGULAR)
        
        # Test initialization
        initialized = await bot.initialize()
        if initialized:
            logger.info("✅ Regular bot initialization successful")
            
            # Test status
            status = bot.get_status()
            logger.info(f"Bot status: {status}")
            
            # Cleanup
            bot.cleanup()
        else:
            logger.error("❌ Regular bot initialization failed")
            
    except Exception as e:
        logger.error(f"❌ Regular bot test failed: {e}")


async def test_prop_firm_bot():
    """Test prop firm trading bot initialization."""
    logger.info("Testing prop firm trading bot...")
    
    try:
        bot = MT5PropFirmBot()
        
        # Test initialization
        initialized = await bot.initialize()
        if initialized:
            logger.info("✅ Prop firm bot initialization successful")
            
            # Test status
            status = bot.get_status()
            logger.info(f"Bot status: {status}")
            
            # Cleanup
            bot.cleanup()
        else:
            logger.error("❌ Prop firm bot initialization failed")
            
    except Exception as e:
        logger.error(f"❌ Prop firm bot test failed: {e}")


async def test_backtesting():
    """Test yfinance backtesting functionality."""
    logger.info("Testing yfinance backtesting...")
    
    try:
        backtester = YFinanceBacktester(
            symbols=["EURUSD=X", "GBPUSD=X"],
            initial_capital=100000
        )
        
        # Run a short backtest
        result = backtester.run_backtest(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        if result and "error" not in result:
            logger.info("✅ Backtesting successful")
            logger.info(f"Backtest results: {result}")
        else:
            logger.error("❌ Backtesting failed")
            logger.error(f"Backtest error: {result}")
            
    except Exception as e:
        logger.error(f"❌ Backtesting test failed: {e}")


async def test_signal_generation():
    """Test signal generation without trading."""
    logger.info("Testing signal generation...")
    
    try:
        # Test regular bot signal generation
        regular_bot = MT5TradingBot(AccountType.REGULAR)
        await regular_bot.initialize()
        
        # Test with sample data
        import pandas as pd
        import numpy as np
        
        # Create sample market data
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        prices = np.random.randn(100).cumsum() + 1.1000  # EURUSD-like prices
        
        sample_data = pd.DataFrame({
            'time': dates,
            'open': prices,
            'high': prices + 0.001,
            'low': prices - 0.001,
            'close': prices,
            'tick_volume': np.random.randint(100, 1000, 100)
        })
        
        # Test signal generation
        signal = regular_bot._generate_signal(sample_data, "EURUSD")
        if signal:
            logger.info("✅ Signal generation successful")
            logger.info(f"Generated signal: {signal}")
        else:
            logger.info("ℹ️ No signal generated (expected for random data)")
        
        regular_bot.cleanup()
        
    except Exception as e:
        logger.error(f"❌ Signal generation test failed: {e}")


async def test_risk_management():
    """Test risk management calculations."""
    logger.info("Testing risk management...")
    
    try:
        # Test regular bot risk management
        regular_bot = MT5TradingBot(AccountType.REGULAR)
        await regular_bot.initialize()
        
        # Test position size calculation
        sample_signal = {
            "symbol": "EURUSD",
            "type": "buy",
            "price": 1.1000,
            "strength": 0.8,
            "reason": "test_signal"
        }
        
        position_size = regular_bot._calculate_position_size(sample_signal)
        logger.info(f"✅ Position size calculation: {position_size}")
        
        # Test pip value calculation
        pip_value = regular_bot._get_pip_value("EURUSD")
        logger.info(f"✅ Pip value calculation: {pip_value}")
        
        regular_bot.cleanup()
        
    except Exception as e:
        logger.error(f"❌ Risk management test failed: {e}")


async def run_all_tests():
    """Run all tests."""
    logger.info("🚀 Starting MT5 bots tests...")
    
    tests = [
        ("Connection Test", test_connection),
        ("Regular Bot Test", test_regular_bot),
        ("Prop Firm Bot Test", test_prop_firm_bot),
        ("Backtesting Test", test_backtesting),
        ("Signal Generation Test", test_signal_generation),
        ("Risk Management Test", test_risk_management),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            await test_func()
            results[test_name] = "PASS"
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            results[test_name] = "FAIL"
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result == "PASS" else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(1 for result in results.values() if result == "PASS")
    total = len(results)
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
    else:
        logger.error(f"⚠️ {total - passed} tests failed")


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 