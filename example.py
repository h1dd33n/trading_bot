"""
Example script demonstrating the mean reversion strategy.
"""

import pandas as pd
import asyncio
from data.data_manager import DataManager
from strategies.strategy_manager import StrategyManager
from config import get_settings

def should_trade(df, threshold=0.01):
    """Original should_trade function provided by user."""
    ma = df['Close'].rolling(window=20).mean()
    last_price = df['Close'].iloc[-1]
    last_ma = ma.iloc[-1]

    if last_price < last_ma * (1 - threshold):
        return "BUY"
    elif last_price > last_ma * (1 + threshold):
        return "SELL"
    return "HOLD"

async def demonstrate_strategy():
    """Demonstrate the mean reversion strategy."""
    
    print("Mean Reversion Strategy Demonstration")
    print("=" * 50)
    
    # Initialize components
    dm = DataManager()
    sm = StrategyManager()
    settings = get_settings()
    
    # Test symbols
    symbols = ["EURAUD=X", "EURCAD=X"]
    
    for symbol in symbols:
        print(f"\n📊 Analyzing {symbol}")
        print("-" * 40)
        
        try:
            # Fetch data
            print(f"Fetching data for {symbol}...")
            data = await dm.fetch_historical_data(symbol, "6mo", "1h")
            
            if data.empty:
                print(f"❌ No data available for {symbol}")
                continue
            
            print(f"✅ Fetched {len(data)} records")
            
            # Calculate indicators
            data = await dm.calculate_indicators(data, symbol)
            
            # Test original should_trade function
            print(f"\n🔍 Testing original should_trade function:")
            
            # Test with different thresholds
            thresholds = [0.01, 0.02, 0.005]
            
            for threshold in thresholds:
                print(f"\n  Threshold: {threshold} ({threshold*100:.1f}%)")
                
                # Get recent data
                recent_data = data.tail(30)
                
                if not recent_data.empty:
                    # Test original function
                    original_signal = should_trade(recent_data, threshold)
                    
                    # Test our implementation
                    strategy = sm.strategies['mean_reversion']
                    our_signal = strategy.should_trade(recent_data, threshold)
                    
                    # Get latest values
                    latest_price = recent_data['Close'].iloc[-1]
                    ma = recent_data['Close'].rolling(window=20).mean()
                    latest_ma = ma.iloc[-1]
                    
                    if not pd.isna(latest_ma):
                        distance = (latest_price - latest_ma) / latest_ma
                        
                        print(f"    Current Price: {latest_price:.4f}")
                        print(f"    Moving Average: {latest_ma:.4f}")
                        print(f"    Distance: {distance:.4f} ({distance*100:.2f}%)")
                        print(f"    Original Signal: {original_signal}")
                        print(f"    Our Signal: {our_signal}")
                        
                        # Verify signals match
                        if original_signal == our_signal:
                            print(f"    ✅ Signals match!")
                        else:
                            print(f"    ❌ Signals don't match!")
            
            # Test signal generation with our strategy
            print(f"\n🚀 Testing full signal generation:")
            signals = await sm.generate_signals({symbol: data})
            
            if signals:
                print(f"  Generated {len(signals)} signals:")
                for i, signal in enumerate(signals[-3:], 1):  # Show last 3 signals
                    print(f"    Signal {i}: {signal.signal_type} at {signal.price:.4f}")
                    print(f"      Confidence: {signal.confidence:.2f}")
                    print(f"      Strength: {signal.strength}")
            else:
                print("  No signals generated")
            
            # Show some statistics
            print(f"\n📈 Data Statistics:")
            print(f"  Total records: {len(data)}")
            print(f"  Date range: {data.index.min()} to {data.index.max()}")
            print(f"  Price range: {data['Close'].min():.4f} - {data['Close'].max():.4f}")
            print(f"  Current price: {data['Close'].iloc[-1]:.4f}")
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demonstration completed!")
    print("\nStrategy Summary:")
    print("- Uses 20-period moving average")
    print("- BUY when price < MA * (1 - threshold)")
    print("- SELL when price > MA * (1 + threshold)")
    print("- HOLD when price is within threshold")
    print("- Default threshold: 1% (0.01)")

if __name__ == "__main__":
    asyncio.run(demonstrate_strategy()) 