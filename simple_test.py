"""
Simple test script for the mean reversion strategy.
"""

import asyncio
import pandas as pd
from data.data_manager import DataManager
from strategies.strategy_manager import StrategyManager
from config import get_settings

async def test_mean_reversion():
    """Test the mean reversion strategy with EURAUR=X and EURAUD=X."""
    
    print("Testing Mean Reversion Strategy")
    print("=" * 50)
    
    # Initialize components
    dm = DataManager()
    sm = StrategyManager()
    settings = get_settings()
    
    # Test symbols
    symbols = ["EURAUD=X", "EURCAD=X"]
    
    for symbol in symbols:
        print(f"\nTesting {symbol}:")
        print("-" * 30)
        
        try:
            # Fetch historical data
            print(f"Fetching data for {symbol}...")
            data = await dm.fetch_historical_data(symbol, "3mo", "1h")
            
            if data.empty:
                print(f"No data found for {symbol}")
                continue
            
            print(f"Fetched {len(data)} records")
            
            # Calculate indicators
            data = await dm.calculate_indicators(data, symbol)
            
            # Test the should_trade function
            strategy = sm.strategies['mean_reversion']
            
            # Test with different thresholds
            thresholds = [0.01, 0.02, 0.005]
            
            for threshold in thresholds:
                print(f"\nTesting with threshold {threshold}:")
                
                # Get the last 50 data points for testing
                test_data = data.tail(50)
                
                if not test_data.empty:
                    # Test the should_trade function
                    signal = strategy.should_trade(test_data, threshold)
                    print(f"Signal: {signal}")
                    
                    # Get latest price and moving average
                    latest_price = test_data['Close'].iloc[-1]
                    ma = test_data['Close'].rolling(window=settings.strategy.lookback_window).mean()
                    latest_ma = ma.iloc[-1]
                    
                    if not pd.isna(latest_ma):
                        distance = (latest_price - latest_ma) / latest_ma
                        print(f"Current Price: {latest_price:.4f}")
                        print(f"Moving Average: {latest_ma:.4f}")
                        print(f"Distance from MA: {distance:.4f} ({distance*100:.2f}%)")
                        
                        if signal == "BUY":
                            print("✅ BUY signal - Price below moving average")
                        elif signal == "SELL":
                            print("🔴 SELL signal - Price above moving average")
                        else:
                            print("⏸️ HOLD signal - Price within threshold")
                    else:
                        print("❌ Not enough data for moving average calculation")
            
            # Test signal generation
            print(f"\nTesting signal generation:")
            signals = await sm.generate_signals({symbol: data})
            
            if signals:
                for signal in signals:
                    print(f"Generated signal: {signal.signal_type} at {signal.price:.4f}")
                    print(f"Confidence: {signal.confidence:.2f}")
                    print(f"Strength: {signal.strength}")
            else:
                print("No signals generated")
                
        except Exception as e:
            print(f"Error testing {symbol}: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_mean_reversion()) 