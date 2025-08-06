"""
Comprehensive Parameter Testing for Mean Reversion Strategy
Tests different parameters, risk management, and timeframes to optimize success rate.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import structlog
from data.data_manager import DataManager
from strategies.strategy_manager import StrategyManager
from config import get_settings, update_strategy_params

logger = structlog.get_logger()

@dataclass
class TestResult:
    """Result of a parameter test."""
    parameters: Dict[str, Any]
    starting_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    avg_trade_return: float
    best_trade: float
    worst_trade: float
    avg_holding_period: float
    compound_return: float
    risk_adjusted_return: float


class ParameterTester:
    """Comprehensive parameter testing for mean reversion strategy."""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.strategy_manager = StrategyManager()
        self.settings = get_settings()
        self.results = []
    
    async def test_parameters(
        self,
        symbols: List[str],
        timeframe: str = "1y",
        interval: str = "1d",
        test_configs: List[Dict[str, Any]] = None
    ) -> List[TestResult]:
        """Test different parameter configurations."""
        
        print(f"🧪 Parameter Testing for {symbols}")
        print(f"📊 Timeframe: {timeframe}, Interval: {interval}")
        print("=" * 60)
        
        if test_configs is None:
            test_configs = self._generate_test_configs()
        
        results = []
        
        for i, config in enumerate(test_configs, 1):
            print(f"\n🔬 Test {i}/{len(test_configs)}: {config['name']}")
            print("-" * 40)
            
            try:
                # Update strategy parameters
                update_strategy_params(config['params'])
                
                # Run backtest simulation
                result = await self._run_backtest_simulation(
                    symbols, timeframe, interval, config
                )
                
                if result:
                    results.append(result)
                    self._print_test_result(result)
                
            except Exception as e:
                logger.error(f"Error in test {i}: {e}")
                continue
        
        return results
    
    def _generate_test_configs(self) -> List[Dict[str, Any]]:
        """Generate different parameter configurations to test."""
        
        configs = []
        
        # Base configurations
        base_configs = [
            {
                "name": "Conservative (Low Risk)",
                "params": {
                    "lookback_window": 20,
                    "threshold": 0.02,
                    "position_size_pct": 0.01,
                    "stop_loss_pct": 0.03,
                    "take_profit_pct": 0.06
                }
            },
            {
                "name": "Moderate (Balanced)",
                "params": {
                    "lookback_window": 20,
                    "threshold": 0.01,
                    "position_size_pct": 0.02,
                    "stop_loss_pct": 0.05,
                    "take_profit_pct": 0.10
                }
            },
            {
                "name": "Aggressive (High Risk)",
                "params": {
                    "lookback_window": 20,
                    "threshold": 0.005,
                    "position_size_pct": 0.05,
                    "stop_loss_pct": 0.08,
                    "take_profit_pct": 0.15
                }
            }
        ]
        
        # Lookback window variations
        lookback_configs = [
            {"name": f"Lookback {period}", "params": {"lookback_window": period}}
            for period in [10, 15, 20, 25, 30, 40, 50]
        ]
        
        # Threshold variations
        threshold_configs = [
            {"name": f"Threshold {thresh*100:.1f}%", "params": {"threshold": thresh}}
            for thresh in [0.005, 0.01, 0.015, 0.02, 0.025, 0.03]
        ]
        
        # Position size variations
        position_configs = [
            {"name": f"Position {size*100:.1f}%", "params": {"position_size_pct": size}}
            for size in [0.01, 0.02, 0.03, 0.05, 0.08, 0.10]
        ]
        
        # Risk management variations
        risk_configs = [
            {
                "name": f"Risk {sl*100:.0f}%/{tp*100:.0f}%",
                "params": {"stop_loss_pct": sl, "take_profit_pct": tp}
            }
            for sl, tp in [(0.03, 0.06), (0.05, 0.10), (0.08, 0.15), (0.10, 0.20)]
        ]
        
        # Compound all configurations
        all_configs = base_configs + lookback_configs + threshold_configs + position_configs + risk_configs
        
        # Add compound configurations
        compound_configs = [
            {
                "name": "Compound Conservative",
                "params": {
                    "lookback_window": 25,
                    "threshold": 0.015,
                    "position_size_pct": 0.015,
                    "stop_loss_pct": 0.04,
                    "take_profit_pct": 0.08
                }
            },
            {
                "name": "Compound Aggressive",
                "params": {
                    "lookback_window": 15,
                    "threshold": 0.008,
                    "position_size_pct": 0.04,
                    "stop_loss_pct": 0.06,
                    "take_profit_pct": 0.12
                }
            }
        ]
        
        # Add custom parameters test (your original settings)
        custom_configs = [
            {
                "name": "Custom Parameters (Your Settings)",
                "params": {
                    "lookback_window": 50,
                    "threshold": 0.03,
                    "position_size_pct": 0.02,
                    "stop_loss_pct": 0.05,
                    "take_profit_pct": 0.10
                }
            }
        ]
        
        return all_configs + compound_configs + custom_configs
    
    async def _run_backtest_simulation(
        self,
        symbols: List[str],
        timeframe: str,
        interval: str,
        config: Dict[str, Any]
    ) -> TestResult:
        """Run a backtest simulation with given parameters."""
        
        try:
            # Fetch data for all symbols
            all_data = {}
            for symbol in symbols:
                data = await self.data_manager.fetch_historical_data(symbol, timeframe, interval)
                if not data.empty:
                    data = await self.data_manager.calculate_indicators(data, symbol)
                    all_data[symbol] = data
            
            if not all_data:
                return None
            
            # Simulate trading
            portfolio_value = 100000.0  # Starting capital
            initial_capital = portfolio_value
            positions = {}
            trades = []
            equity_curve = []
            
            # Get combined timeline
            all_dates = set()
            for data in all_data.values():
                all_dates.update(data.index)
            timeline = sorted(all_dates)
            
            for date in timeline:
                # Update portfolio with current prices
                for symbol, data in all_data.items():
                    if date in data.index:
                        current_price = data.loc[date, 'Close']
                        
                        # Update existing positions
                        if symbol in positions:
                            position = positions[symbol]
                            unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
                            position['unrealized_pnl'] = unrealized_pnl
                            
                            # Check stop loss / take profit
                            if self._should_exit_position(position, current_price):
                                # Close position
                                exit_price = current_price
                                pnl = (exit_price - position['entry_price']) * position['quantity']
                                portfolio_value += pnl
                                
                                trades.append({
                                    'symbol': symbol,
                                    'entry_date': position['entry_date'],
                                    'exit_date': date,
                                    'entry_price': position['entry_price'],
                                    'exit_price': exit_price,
                                    'quantity': position['quantity'],
                                    'pnl': pnl,
                                    'pnl_pct': pnl / (position['entry_price'] * position['quantity'])
                                })
                                
                                del positions[symbol]
                
                # Generate signals for new positions
                for symbol, data in all_data.items():
                    if date in data.index and symbol not in positions:
                        # Get data up to current date
                        historical_data = data.loc[:date]
                        if len(historical_data) >= self.settings.strategy.lookback_window:
                            signal = self._generate_signal(historical_data)
                            
                            if signal in ['BUY', 'SELL']:
                                # Calculate position size
                                position_size = portfolio_value * self.settings.strategy.position_size_pct
                                quantity = position_size / current_price
                                
                                # Open position
                                positions[symbol] = {
                                    'entry_date': date,
                                    'entry_price': current_price,
                                    'quantity': quantity,
                                    'type': signal,
                                    'unrealized_pnl': 0
                                }
                
                # Record equity curve
                total_value = portfolio_value
                for position in positions.values():
                    total_value += position['unrealized_pnl']
                
                equity_curve.append({
                    'date': date,
                    'total_value': total_value,
                    'cash': portfolio_value,
                    'positions': len(positions)
                })
            
            # Close remaining positions at last price
            for symbol, position in positions.items():
                if symbol in all_data and len(all_data[symbol]) > 0:
                    last_price = all_data[symbol].iloc[-1]['Close']
                    pnl = (last_price - position['entry_price']) * position['quantity']
                    portfolio_value += pnl
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_date': position['entry_date'],
                        'exit_date': timeline[-1],
                        'entry_price': position['entry_price'],
                        'exit_price': last_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'pnl_pct': pnl / (position['entry_price'] * position['quantity'])
                    })
            
            # Calculate final capital
            final_capital = portfolio_value
            for position in positions.values():
                if position['type'] == 'BUY':
                    final_capital += position['unrealized_pnl']
                else:  # SELL position
                    final_capital -= position['unrealized_pnl']
            
            # Calculate metrics
            return self._calculate_metrics(
                trades, equity_curve, initial_capital, final_capital, config
            )
            
        except Exception as e:
            logger.error(f"Error in backtest simulation: {e}")
            return None
    
    def _generate_signal(self, data: pd.DataFrame) -> str:
        """Generate trading signal based on current strategy."""
        if data.empty or len(data) < self.settings.strategy.lookback_window:
            return "HOLD"
        
        try:
            ma = data['Close'].rolling(window=self.settings.strategy.lookback_window).mean()
            last_price = data['Close'].iloc[-1]
            last_ma = ma.iloc[-1]
            
            if pd.isna(last_ma):
                return "HOLD"
            
            threshold = self.settings.strategy.threshold
            
            if last_price < last_ma * (1 - threshold):
                return "BUY"
            elif last_price > last_ma * (1 + threshold):
                return "SELL"
            return "HOLD"
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return "HOLD"
    
    def _should_exit_position(self, position: Dict, current_price: float) -> bool:
        """Check if position should be closed due to stop loss or take profit."""
        entry_price = position['entry_price']
        position_type = position['type']
        
        if position_type == 'BUY':
            stop_loss = entry_price * (1 - self.settings.strategy.stop_loss_pct)
            take_profit = entry_price * (1 + self.settings.strategy.take_profit_pct)
            
            return current_price <= stop_loss or current_price >= take_profit
        
        elif position_type == 'SELL':
            stop_loss = entry_price * (1 + self.settings.strategy.stop_loss_pct)
            take_profit = entry_price * (1 - self.settings.strategy.take_profit_pct)
            
            return current_price >= stop_loss or current_price <= take_profit
        
        return False
    
    def _calculate_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[Dict],
        initial_capital: float,
        final_capital: float,
        config: Dict[str, Any]
    ) -> TestResult:
        """Calculate comprehensive trading metrics."""
        
        if not trades:
            return TestResult(
                parameters=config['params'],
                starting_capital=initial_capital,
                final_capital=initial_capital,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_return=0.0,
                total_return_pct=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                profit_factor=0.0,
                avg_trade_return=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                avg_holding_period=0.0,
                compound_return=0.0,
                risk_adjusted_return=0.0
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Return metrics
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = total_pnl
        total_return_pct = total_return / initial_capital
        
        # Trade analysis
        pnls = [t['pnl'] for t in trades]
        avg_trade_return = np.mean(pnls) if pnls else 0.0
        best_trade = max(pnls) if pnls else 0.0
        worst_trade = min(pnls) if pnls else 0.0
        
        # Holding period analysis
        holding_periods = []
        for trade in trades:
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            holding_period = (exit_date - entry_date).days
            holding_periods.append(holding_period)
        
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0.0
        
        # Risk metrics
        if equity_curve:
            equity_df = pd.DataFrame(equity_curve)
            equity_df['date'] = pd.to_datetime(equity_df['date'])
            equity_df = equity_df.set_index('date').sort_index()
            
            # Calculate drawdown
            equity_df['peak'] = equity_df['total_value'].expanding().max()
            equity_df['drawdown'] = (equity_df['total_value'] - equity_df['peak']) / equity_df['peak']
            max_drawdown = abs(equity_df['drawdown'].min())
            
            # Calculate Sharpe ratio
            returns = equity_df['total_value'].pct_change().dropna()
            if len(returns) > 0:
                sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0.0
            else:
                sharpe_ratio = 0.0
            
            # Compound return
            final_value = equity_df['total_value'].iloc[-1]
            compound_return = (final_value / initial_capital) - 1
        else:
            max_drawdown = 0.0
            sharpe_ratio = 0.0
            compound_return = total_return_pct
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Risk-adjusted return
        risk_adjusted_return = compound_return / max_drawdown if max_drawdown > 0 else compound_return
        
        return TestResult(
            parameters=config['params'],
            starting_capital=initial_capital,
            final_capital=final_capital,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            avg_trade_return=avg_trade_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_holding_period=avg_holding_period,
            compound_return=compound_return,
            risk_adjusted_return=risk_adjusted_return
        )
    
    def _print_test_result(self, result: TestResult):
        """Print test result in a formatted way."""
        print(f"📈 Results:")
        print(f"   Starting Capital: ${result.starting_capital:,.2f}")
        print(f"   Final Capital: ${result.final_capital:,.2f}")
        print(f"   Capital Growth: ${result.final_capital - result.starting_capital:,.2f}")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Win Rate: {result.win_rate:.2%}")
        print(f"   Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2%})")
        print(f"   Compound Return: {result.compound_return:.2%}")
        print(f"   Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   Profit Factor: {result.profit_factor:.2f}")
        print(f"   Risk-Adjusted Return: {result.risk_adjusted_return:.2f}")
        print(f"   Avg Trade Return: ${result.avg_trade_return:,.2f}")
        print(f"   Best Trade: ${result.best_trade:,.2f}")
        print(f"   Worst Trade: ${result.worst_trade:,.2f}")
        print(f"   Avg Holding Period: {result.avg_holding_period:.1f} days")
    
    def print_summary(self, results: List[TestResult]):
        """Print summary of all test results."""
        if not results:
            print("No results to display.")
            return
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        # Sort by different metrics
        metrics = [
            ('Total Return %', 'total_return_pct', True),
            ('Win Rate', 'win_rate', True),
            ('Sharpe Ratio', 'sharpe_ratio', True),
            ('Risk-Adjusted Return', 'risk_adjusted_return', True),
            ('Profit Factor', 'profit_factor', True),
            ('Max Drawdown', 'max_drawdown', False)
        ]
        
        for metric_name, metric_attr, reverse in metrics:
            sorted_results = sorted(results, key=lambda x: getattr(x, metric_attr), reverse=reverse)
            best = sorted_results[0]
            
            print(f"\n🏆 Best by {metric_name}:")
            print(f"   {best.parameters}")
            print(f"   {metric_name}: {getattr(best, metric_attr):.4f}")
            print(f"   Starting Capital: ${best.starting_capital:,.2f}")
            print(f"   Final Capital: ${best.final_capital:,.2f}")
            print(f"   Total Return: {best.total_return_pct:.2%}")
            print(f"   Win Rate: {best.win_rate:.2%}")
            print(f"   Trades: {best.total_trades}")
        
        # Overall statistics
        print(f"\n📈 Overall Statistics:")
        print(f"   Tests Run: {len(results)}")
        print(f"   Average Return: {np.mean([r.total_return_pct for r in results]):.2%}")
        print(f"   Average Win Rate: {np.mean([r.win_rate for r in results]):.2%}")
        print(f"   Average Sharpe: {np.mean([r.sharpe_ratio for r in results]):.2f}")
        
        # Risk analysis
        profitable_tests = [r for r in results if r.total_return_pct > 0]
        if profitable_tests:
            print(f"\n💰 Profitable Tests: {len(profitable_tests)}/{len(results)}")
            print(f"   Best Return: {max([r.total_return_pct for r in profitable_tests]):.2%}")
            print(f"   Average Profitable Return: {np.mean([r.total_return_pct for r in profitable_tests]):.2%}")
        
        # Capital summary
        print(f"\n💵 Capital Summary:")
        best_capital_growth = max(results, key=lambda x: x.final_capital)
        print(f"   Best Final Capital: ${best_capital_growth.final_capital:,.2f} (${best_capital_growth.starting_capital:,.2f} → ${best_capital_growth.final_capital:,.2f})")
        print(f"   Average Final Capital: ${np.mean([r.final_capital for r in results]):,.2f}")
        print(f"   Average Capital Growth: ${np.mean([r.final_capital - r.starting_capital for r in results]):,.2f}")
        
        # Highlight custom parameters test
        custom_results = [r for r in results if "Custom Parameters" in str(r.parameters)]
        if custom_results:
            custom_result = custom_results[0]
            print(f"\n🎯 Your Custom Parameters Test:")
            print(f"   Parameters: {custom_result.parameters}")
            print(f"   Starting Capital: ${custom_result.starting_capital:,.2f}")
            print(f"   Final Capital: ${custom_result.final_capital:,.2f}")
            print(f"   Capital Growth: ${custom_result.final_capital - custom_result.starting_capital:,.2f}")
            print(f"   Total Return: {custom_result.total_return_pct:.2%}")
            print(f"   Win Rate: {custom_result.win_rate:.2%}")
            print(f"   Total Trades: {custom_result.total_trades}")
            print(f"   Sharpe Ratio: {custom_result.sharpe_ratio:.2f}")
            print(f"   Max Drawdown: {custom_result.max_drawdown:.2%}")


async def main():
    """Main testing function."""
    
    print("🧪 Comprehensive Parameter Testing")
    print("=" * 60)
    
    # Initialize tester
    tester = ParameterTester()
    
    # Get user input
    print("\n📋 Test Configuration:")
    
    # Symbol selection
    symbols = ["EURAUD=X", "EURCAD=X"]
    print(f"Symbols: {symbols}")
    
    # Timeframe selection
    print("\n⏰ Timeframe Options:")
    print("1. 1 Year (1y)")
    print("2. 2 Years (2y)")
    print("3. 5 Years (5y)")
    print("4. 10 Years (10y)")
    
    timeframe_choice = input("Select timeframe (1-4): ").strip()
    timeframe_map = {
        "1": "1y",
        "2": "2y", 
        "3": "5y",
        "4": "10y"
    }
    timeframe = timeframe_map.get(timeframe_choice, "1y")
    
    print(f"Selected timeframe: {timeframe}")
    
    # Run tests
    print(f"\n🚀 Starting parameter tests...")
    results = await tester.test_parameters(
        symbols=symbols,
        timeframe=timeframe,
        interval="1d"
    )
    
    # Print summary
    if results:
        tester.print_summary(results)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"parameter_test_results_{timestamp}.csv"
        
        # Convert results to DataFrame
        results_data = []
        for result in results:
            row = {
                'name': f"Test_{results.index(result)}",
                **result.parameters,
                'starting_capital': result.starting_capital,
                'final_capital': result.final_capital,
                'capital_growth': result.final_capital - result.starting_capital,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'total_return': result.total_return,
                'total_return_pct': result.total_return_pct,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'profit_factor': result.profit_factor,
                'avg_trade_return': result.avg_trade_return,
                'best_trade': result.best_trade,
                'worst_trade': result.worst_trade,
                'avg_holding_period': result.avg_holding_period,
                'compound_return': result.compound_return,
                'risk_adjusted_return': result.risk_adjusted_return
            }
            results_data.append(row)
        
        df = pd.DataFrame(results_data)
        df.to_csv(filename, index=False)
        print(f"\n💾 Results saved to: {filename}")
        
    else:
        print("❌ No results generated. Check your configuration.")


if __name__ == "__main__":
    asyncio.run(main()) 