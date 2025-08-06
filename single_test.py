"""
Single Parameter Test for Mean Reversion Strategy
Tests current parameters from config.py on a specific time period.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
import structlog
from data.data_manager import DataManager
from strategies.strategy_manager import StrategyManager
from config import get_settings

logger = structlog.get_logger()

@dataclass
class SingleTestResult:
    """Result of a single parameter test."""
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_percentage: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_return: float
    best_trade: float
    worst_trade: float
    avg_holding_period: float
    parameters_used: Dict[str, Any]


class SingleParameterTester:
    """Single parameter test using current config.py settings."""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.strategy_manager = StrategyManager()
        self.settings = get_settings()
    
    async def test_current_parameters(
        self,
        symbols: List[str],
        timeframe: str = "2y",
        interval: str = "1d"
    ) -> SingleTestResult:
        """Test current parameters from config.py."""
        
        print(f"🧪 Single Parameter Test")
        print(f"📊 Symbols: {symbols}")
        print(f"📅 Timeframe: {timeframe}, Interval: {interval}")
        print("=" * 60)
        
        # Print current parameters
        print(f"\n⚙️ Current Parameters from config.py:")
        print(f"   Lookback Window: {self.settings.strategy.lookback_window}")
        print(f"   Threshold: {self.settings.strategy.threshold:.3f} ({self.settings.strategy.threshold*100:.1f}%)")
        print(f"   Position Size: {self.settings.strategy.position_size_pct:.3f} ({self.settings.strategy.position_size_pct*100:.1f}%)")
        print(f"   Stop Loss: {self.settings.strategy.stop_loss_pct:.3f} ({self.settings.strategy.stop_loss_pct*100:.1f}%)")
        print(f"   Take Profit: {self.settings.strategy.take_profit_pct:.3f} ({self.settings.strategy.take_profit_pct*100:.1f}%)")
        
        try:
            # Fetch data for all symbols
            all_data = {}
            for symbol in symbols:
                print(f"\n📈 Fetching data for {symbol}...")
                data = await self.data_manager.fetch_historical_data(symbol, timeframe, interval)
                if not data.empty:
                    data = await self.data_manager.calculate_indicators(data, symbol)
                    all_data[symbol] = data
                    print(f"   ✅ {symbol}: {len(data)} data points from {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
                else:
                    print(f"   ❌ {symbol}: No data available")
            
            if not all_data:
                print("❌ No data available for any symbol")
                return None
            
            # Run backtest simulation
            result = await self._run_single_backtest(all_data)
            
            if result:
                self._print_detailed_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in single parameter test: {e}")
            print(f"❌ Error: {e}")
            return None
    
    async def _run_single_backtest(self, all_data: Dict[str, pd.DataFrame]) -> SingleTestResult:
        """Run a single backtest with current parameters."""
        
        # Simulate trading
        initial_balance = 100000.0  # Starting capital
        portfolio_value = initial_balance
        positions = {}
        trades = []
        equity_curve = []
        
        # Get combined timeline
        all_dates = set()
        for data in all_data.values():
            all_dates.update(data.index)
        timeline = sorted(all_dates)
        
        print(f"\n📊 Trading Simulation:")
        print(f"   Initial Balance: ${initial_balance:,.2f}")
        print(f"   Trading Period: {timeline[0].strftime('%Y-%m-%d')} to {timeline[-1].strftime('%Y-%m-%d')}")
        print(f"   Total Days: {len(timeline)}")
        
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
        
        # Calculate final balance
        final_balance = portfolio_value
        for position in positions.values():
            if position['type'] == 'BUY':
                final_balance += position['unrealized_pnl']
            else:  # SELL position
                final_balance -= position['unrealized_pnl']
        
        # Calculate metrics
        return self._calculate_single_metrics(
            trades, equity_curve, initial_balance, final_balance
        )
    
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
    
    def _calculate_single_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[Dict],
        initial_balance: float,
        final_balance: float
    ) -> SingleTestResult:
        """Calculate metrics for single test."""
        
        if not trades:
            return SingleTestResult(
                initial_balance=initial_balance,
                final_balance=initial_balance,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_percentage=0.0,
                total_return=0.0,
                total_return_pct=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                avg_trade_return=0.0,
                best_trade=0.0,
                worst_trade=0.0,
                avg_holding_period=0.0,
                parameters_used={
                    'lookback_window': self.settings.strategy.lookback_window,
                    'threshold': self.settings.strategy.threshold,
                    'position_size_pct': self.settings.strategy.position_size_pct,
                    'stop_loss_pct': self.settings.strategy.stop_loss_pct,
                    'take_profit_pct': self.settings.strategy.take_profit_pct
                }
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_percentage = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        # Return metrics
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = total_pnl
        total_return_pct = (total_return / initial_balance) * 100
        
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
            max_drawdown = abs(equity_df['drawdown'].min()) * 100
            
            # Calculate Sharpe ratio
            returns = equity_df['total_value'].pct_change().dropna()
            if len(returns) > 0:
                sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            max_drawdown = 0.0
            sharpe_ratio = 0.0
        
        return SingleTestResult(
            initial_balance=initial_balance,
            final_balance=final_balance,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_percentage=win_percentage,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            avg_trade_return=avg_trade_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_holding_period=avg_holding_period,
            parameters_used={
                'lookback_window': self.settings.strategy.lookback_window,
                'threshold': self.settings.strategy.threshold,
                'position_size_pct': self.settings.strategy.position_size_pct,
                'stop_loss_pct': self.settings.strategy.stop_loss_pct,
                'take_profit_pct': self.settings.strategy.take_profit_pct
            }
        )
    
    def _print_detailed_results(self, result: SingleTestResult):
        """Print detailed test results."""
        print("\n" + "=" * 80)
        print("📊 SINGLE PARAMETER TEST RESULTS")
        print("=" * 80)
        
        # Balance Summary
        print(f"\n💰 BALANCE SUMMARY:")
        print(f"   Initial Balance: ${result.initial_balance:,.2f}")
        print(f"   Final Balance: ${result.final_balance:,.2f}")
        print(f"   Balance Change: ${result.final_balance - result.initial_balance:,.2f}")
        print(f"   Total Return: ${result.total_return:,.2f}")
        print(f"   Return Percentage: {result.total_return_pct:.2f}%")
        
        # Trading Performance
        print(f"\n📈 TRADING PERFORMANCE:")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Winning Trades: {result.winning_trades}")
        print(f"   Losing Trades: {result.losing_trades}")
        print(f"   Win Percentage: {result.win_percentage:.2f}%")
        print(f"   Average Trade Return: ${result.avg_trade_return:,.2f}")
        print(f"   Best Trade: ${result.best_trade:,.2f}")
        print(f"   Worst Trade: ${result.worst_trade:,.2f}")
        print(f"   Average Holding Period: {result.avg_holding_period:.1f} days")
        
        # Risk Metrics
        print(f"\n⚠️ RISK METRICS:")
        print(f"   Maximum Drawdown: {result.max_drawdown:.2f}%")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        
        # Parameters Used
        print(f"\n⚙️ PARAMETERS USED:")
        for param, value in result.parameters_used.items():
            if 'pct' in param:
                print(f"   {param.replace('_', ' ').title()}: {value:.3f} ({value*100:.1f}%)")
            else:
                print(f"   {param.replace('_', ' ').title()}: {value}")
        
        # Performance Summary
        print(f"\n🎯 PERFORMANCE SUMMARY:")
        if result.total_return_pct > 0:
            print(f"   ✅ PROFITABLE: +{result.total_return_pct:.2f}% return")
        else:
            print(f"   ❌ LOSS: {result.total_return_pct:.2f}% return")
        
        if result.win_percentage >= 50:
            print(f"   ✅ Good Win Rate: {result.win_percentage:.2f}%")
        else:
            print(f"   ⚠️ Low Win Rate: {result.win_percentage:.2f}%")
        
        if result.sharpe_ratio > 1.0:
            print(f"   ✅ Good Risk-Adjusted Return: Sharpe {result.sharpe_ratio:.2f}")
        else:
            print(f"   ⚠️ Poor Risk-Adjusted Return: Sharpe {result.sharpe_ratio:.2f}")


async def main():
    """Main testing function."""
    
    print("🧪 Single Parameter Test")
    print("=" * 60)
    
    # Initialize tester
    tester = SingleParameterTester()
    
    # Test configuration
    symbols = ["EURAUD=X", "EURCAD=X"]
    
    # Timeframe options
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
    timeframe = timeframe_map.get(timeframe_choice, "2y")
    
    print(f"Selected timeframe: {timeframe}")
    
    # Run test
    print(f"\n🚀 Starting single parameter test...")
    result = await tester.test_current_parameters(
        symbols=symbols,
        timeframe=timeframe,
        interval="1d"
    )
    
    if result:
        print(f"\n✅ Test completed successfully!")
    else:
        print(f"\n❌ Test failed. Check your configuration.")


if __name__ == "__main__":
    asyncio.run(main()) 