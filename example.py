"""
Example script demonstrating the Advanced Mean Reversion Trading Bot.
This script shows how to use all the main features of the trading bot.
"""

import asyncio
from datetime import datetime, timedelta
import structlog

from test_config import setup_test_environment
from config import get_settings, update_strategy_params
from data.data_manager import get_data_manager
from strategies.strategy_manager import get_strategy_manager
from risk.risk_manager import get_risk_manager
from backtesting.backtest_engine import get_backtest_engine
from optimization.parameter_optimizer import get_optimizer

# Configure logging
logger = structlog.get_logger()


async def example_basic_usage():
    """Example of basic trading bot usage."""
    print("\n" + "="*60)
    print("BASIC USAGE EXAMPLE")
    print("="*60)
    
    # Initialize components
    data_manager = await get_data_manager()
    strategy_manager = await get_strategy_manager()
    risk_manager = await get_risk_manager()
    
    # Fetch data for a symbol
    print("Fetching historical data...")
    data = await data_manager.fetch_historical_data("AAPL", "1mo", "1h")
    
    if not data.empty:
        print(f"Fetched {len(data)} records for AAPL")
        
        # Calculate indicators
        data = await data_manager.calculate_indicators(data, "AAPL")
        print("Calculated technical indicators")
        
        # Generate signals
        signals = await strategy_manager.generate_signals({"AAPL": data})
        print(f"Generated {len(signals)} signals")
        
        # Show signal details
        for signal in signals:
            print(f"Signal: {signal.signal_type} {signal.symbol} @ ${signal.price:.2f}")
            print(f"  Confidence: {signal.confidence:.2f}")
            print(f"  Strength: {signal.strength}")
    
    # Show portfolio summary
    portfolio = risk_manager.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"  Total Value: ${portfolio['total_value']:,.2f}")
    print(f"  Cash: ${portfolio['cash']:,.2f}")
    print(f"  Positions: {portfolio['num_positions']}")


async def example_backtest():
    """Example of running a backtest."""
    print("\n" + "="*60)
    print("BACKTEST EXAMPLE")
    print("="*60)
    
    # Initialize backtest engine
    engine = await get_backtest_engine()
    
    # Run backtest
    print("Running backtest...")
    results = await engine.run_backtest(
        symbols=["AAPL", "MSFT"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 6, 30),
        initial_capital=100000.0
    )
    
    # Print results
    engine.print_summary()
    
    # Show detailed metrics
    print(f"\nDetailed Metrics:")
    print(f"  Total Return: ${results.total_return:,.2f} ({results.total_return_pct:.2%})")
    print(f"  Sharpe Ratio: {results.sharpe_ratio:.2f}")
    print(f"  Max Drawdown: {results.max_drawdown_pct:.2%}")
    print(f"  Win Rate: {results.win_rate:.2%}")
    print(f"  Profit Factor: {results.profit_factor:.2f}")
    print(f"  Total Trades: {results.total_trades}")
    print(f"  Winning Trades: {results.winning_trades}")
    print(f"  Losing Trades: {results.losing_trades}")


async def example_parameter_optimization():
    """Example of parameter optimization."""
    print("\n" + "="*60)
    print("PARAMETER OPTIMIZATION EXAMPLE")
    print("="*60)
    
    # Initialize optimizer
    optimizer = await get_optimizer()
    
    # Define parameter ranges to test
    parameter_ranges = {
        'z_score_threshold': [1.5, 2.0, 2.5],
        'lookback_window': [15, 20, 25],
        'position_size_pct': [0.01, 0.02, 0.03],
        'stop_loss_pct': [0.03, 0.05, 0.07]
    }
    
    print("Running grid search optimization...")
    print(f"Testing {len(parameter_ranges)} parameters with {sum(len(v) for v in parameter_ranges.values())} total combinations")
    
    # Run grid search
    results = await optimizer.grid_search(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 6, 30),
        parameter_ranges=parameter_ranges
    )
    
    # Print top results
    optimizer.print_optimization_results(results, top_n=5)
    
    # Apply best parameters
    if results:
        best_params = results[0].parameters
        print(f"\nApplying best parameters: {best_params}")
        update_strategy_params(best_params)


async def example_strategy_comparison():
    """Example of comparing different strategies."""
    print("\n" + "="*60)
    print("STRATEGY COMPARISON EXAMPLE")
    print("="*60)
    
    engine = await get_backtest_engine()
    
    strategies = ["mean_reversion", "bollinger_bands", "rsi_mean_reversion"]
    results = {}
    
    for strategy in strategies:
        print(f"\nTesting {strategy} strategy...")
        
        # Update strategy
        update_strategy_params({'strategy_type': strategy})
        
        # Run backtest
        result = await engine.run_backtest(
            symbols=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            initial_capital=100000.0
        )
        
        results[strategy] = result
    
    # Compare results
    print("\nStrategy Comparison:")
    print(f"{'Strategy':<20} {'Return %':<10} {'Sharpe':<8} {'Drawdown %':<12} {'Win Rate %':<12}")
    print("-" * 70)
    
    for strategy, result in results.items():
        print(f"{strategy:<20} {result.total_return_pct:>8.2%} {result.sharpe_ratio:>6.2f} "
              f"{result.max_drawdown_pct:>10.2%} {result.win_rate:>10.2%}")


async def example_risk_management():
    """Example of risk management features."""
    print("\n" + "="*60)
    print("RISK MANAGEMENT EXAMPLE")
    print("="*60)
    
    risk_manager = await get_risk_manager()
    
    # Test position sizing
    print("Testing position sizing...")
    quantity = risk_manager.calculate_position_size("AAPL", 150.0, 0.8, 100000.0)
    print(f"Position size for AAPL @ $150: {quantity:.2f} shares")
    
    # Test stop loss and take profit
    print("\nTesting stop loss and take profit...")
    stop_loss, take_profit = risk_manager.calculate_stop_loss_take_profit(100.0, "long")
    print(f"Entry price: $100")
    print(f"Stop loss: ${stop_loss:.2f}")
    print(f"Take profit: ${take_profit:.2f}")
    
    # Test portfolio constraints
    print("\nTesting portfolio constraints...")
    portfolio_summary = risk_manager.get_portfolio_summary()
    print(f"Current portfolio value: ${portfolio_summary['total_value']:,.2f}")
    print(f"Cash: ${portfolio_summary['cash']:,.2f}")
    print(f"Number of positions: {portfolio_summary['num_positions']}")


async def example_live_trading_simulation():
    """Example of live trading simulation."""
    print("\n" + "="*60)
    print("LIVE TRADING SIMULATION EXAMPLE")
    print("="*60)
    
    # Initialize components
    data_manager = await get_data_manager()
    strategy_manager = await get_strategy_manager()
    risk_manager = await get_risk_manager()
    
    # Start real-time data updates
    print("Starting real-time data updates...")
    await data_manager.start_real_time_updates()
    
    # Simulate live trading loop
    print("Simulating live trading...")
    for i in range(5):  # Simulate 5 iterations
        print(f"\nIteration {i+1}:")
        
        # Get latest data
        data_dict = await data_manager.get_multiple_symbols_data(["AAPL", "MSFT"])
        
        # Generate signals
        signals = await strategy_manager.generate_signals(data_dict)
        
        # Process signals
        for signal in signals:
            print(f"  Signal: {signal.signal_type} {signal.symbol} @ ${signal.price:.2f}")
            
            # Calculate position size
            quantity = risk_manager.calculate_position_size(
                signal.symbol, 
                signal.price, 
                signal.confidence,
                risk_manager.portfolio.total_value
            )
            
            if quantity > 0:
                print(f"    Position size: {quantity:.2f} shares")
        
        # Update portfolio
        for symbol, data in data_dict.items():
            if not data.empty:
                latest_price = data.iloc[-1]['Close']
                risk_manager.update_portfolio(symbol, latest_price, datetime.now())
        
        # Show portfolio status
        portfolio = risk_manager.get_portfolio_summary()
        print(f"  Portfolio value: ${portfolio['total_value']:,.2f}")
        
        # Wait between iterations
        await asyncio.sleep(1)
    
    # Stop real-time updates
    await data_manager.stop_real_time_updates()
    print("\nLive trading simulation completed.")


async def main():
    """Run all examples."""
    print("Advanced Mean Reversion Trading Bot - Examples")
    print("="*60)
    
    # Set up test environment
    setup_test_environment()
    
    try:
        # Run examples
        await example_basic_usage()
        await example_backtest()
        await example_parameter_optimization()
        await example_strategy_comparison()
        await example_risk_management()
        await example_live_trading_simulation()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main()) 