"""
Backtesting engine for simulating trading strategies with historical data.
Provides comprehensive performance metrics and analysis.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import structlog
from config import get_settings
from data.data_manager import get_data_manager
from strategies.strategy_manager import get_strategy_manager, SignalType
from risk.risk_manager import get_risk_manager, PositionType

logger = structlog.get_logger()


@dataclass
class BacktestResult:
    """Backtest result data structure."""
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    equity_curve: pd.DataFrame
    trade_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class BacktestEngine:
    """Comprehensive backtesting engine."""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_manager = None
        self.strategy_manager = None
        self.risk_manager = None
        self.results = None
    
    async def initialize(self):
        """Initialize backtesting components."""
        self.data_manager = await get_data_manager()
        self.strategy_manager = await get_strategy_manager()
        self.risk_manager = await get_risk_manager()
    
    async def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0
    ) -> BacktestResult:
        """Run backtest simulation."""
        try:
            logger.info(f"Starting backtest for {symbols} from {start_date} to {end_date}")
            
            # Initialize components
            await self.initialize()
            
            # Reset risk manager for new backtest
            self.risk_manager.portfolio.total_value = initial_capital
            self.risk_manager.portfolio.cash = initial_capital
            self.risk_manager.portfolio.positions = {}
            self.risk_manager.trade_history = []
            self.risk_manager.performance_history = []
            
            # Fetch historical data
            data_dict = await self._fetch_historical_data(symbols, start_date, end_date)
            
            # Run simulation
            equity_curve, trade_history = await self._run_simulation(data_dict, start_date, end_date)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(equity_curve, trade_history)
            
            # Create result object
            self.results = BacktestResult(
                total_return=performance_metrics['total_return'],
                total_return_pct=performance_metrics['total_return_pct'],
                sharpe_ratio=performance_metrics['sharpe_ratio'],
                max_drawdown=performance_metrics['max_drawdown'],
                max_drawdown_pct=performance_metrics['max_drawdown_pct'],
                win_rate=performance_metrics['win_rate'],
                profit_factor=performance_metrics['profit_factor'],
                total_trades=performance_metrics['total_trades'],
                winning_trades=performance_metrics['winning_trades'],
                losing_trades=performance_metrics['losing_trades'],
                avg_win=performance_metrics['avg_win'],
                avg_loss=performance_metrics['avg_loss'],
                best_trade=performance_metrics['best_trade'],
                worst_trade=performance_metrics['worst_trade'],
                equity_curve=equity_curve,
                trade_history=trade_history,
                performance_metrics=performance_metrics
            )
            
            logger.info(f"Backtest completed. Total return: {performance_metrics['total_return_pct']:.2%}")
            return self.results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise
    
    async def _fetch_historical_data(
        self, 
        symbols: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for all symbols."""
        data_dict = {}
        
        for symbol in symbols:
            try:
                # Fetch data with extra buffer for indicators
                buffer_days = max(self.settings.strategy.lookback_window, 30)
                buffer_start = start_date - timedelta(days=buffer_days)
                
                data = await self.data_manager.fetch_historical_data(
                    symbol, 
                    period="1y",  # Fallback period
                    interval="1h",
                    start_date=buffer_start,
                    end_date=end_date
                )
                
                # Filter to date range - handle timezone-aware timestamps
                if not data.empty:
                    # Convert timezone-aware timestamps to naive for comparison
                    data_index = data.index
                    if hasattr(data_index, 'tz_localize'):
                        data_index = data_index.tz_localize(None)
                    elif hasattr(data_index, 'replace'):
                        data_index = data_index.replace(tzinfo=None)
                    
                    # Create a new DataFrame with naive timestamps
                    data = data.copy()
                    data.index = data_index
                    
                    # Filter to date range
                    data = data[(data.index >= buffer_start) & (data.index <= end_date)]
                
                if not data.empty:
                    # Ensure we have the required columns
                    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    if all(col in data.columns for col in required_columns):
                        # Calculate indicators
                        data = await self.data_manager.calculate_indicators(data, symbol)
                        data_dict[symbol] = data
                        logger.info(f"Fetched {len(data)} records for {symbol}")
                    else:
                        logger.warning(f"Missing required columns for {symbol}. Available: {data.columns.tolist()}")
                else:
                    logger.warning(f"No data found for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
        
        return data_dict
    
    async def _run_simulation(
        self, 
        data_dict: Dict[str, pd.DataFrame], 
        start_date: datetime, 
        end_date: datetime
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Run the main simulation loop."""
        try:
            # Get all unique timestamps
            all_timestamps = set()
            for data in data_dict.values():
                all_timestamps.update(data.index)
            
            timestamps = sorted(list(all_timestamps))
            
            # Convert timezone-aware timestamps to naive for comparison
            naive_timestamps = []
            for t in timestamps:
                if hasattr(t, 'tz_localize'):
                    naive_t = t.tz_localize(None)
                elif hasattr(t, 'replace'):
                    naive_t = t.replace(tzinfo=None)
                else:
                    naive_t = t
                naive_timestamps.append(naive_t)
            
            timestamps = [t for t in naive_timestamps if start_date <= t <= end_date]
            
            equity_curve = []
            trade_history = []
            
            logger.info(f"Running simulation for {len(timestamps)} timestamps")
            
            for i, timestamp in enumerate(timestamps):
                if i % 1000 == 0:  # Log progress
                    logger.info(f"Processing timestamp {i}/{len(timestamps)}: {timestamp}")
                
                # Update portfolio with current prices
                for symbol, data in data_dict.items():
                    # Convert timestamp to match data index timezone
                    if hasattr(timestamp, 'tz_localize'):
                        compare_timestamp = timestamp.tz_localize(None)
                    elif hasattr(timestamp, 'replace'):
                        compare_timestamp = timestamp.replace(tzinfo=None)
                    else:
                        compare_timestamp = timestamp
                    
                    if compare_timestamp in data.index:
                        current_price = data.loc[compare_timestamp, 'Close']
                        self.risk_manager.update_portfolio(symbol, current_price, compare_timestamp)
                
                # Check for stop loss/take profit exits
                await self._check_exit_signals(data_dict, timestamp, trade_history)
                
                # Generate new signals
                current_data = {}
                for symbol, data in data_dict.items():
                    # Convert timestamp to match data index timezone
                    if hasattr(timestamp, 'tz_localize'):
                        compare_timestamp = timestamp.tz_localize(None)
                    elif hasattr(timestamp, 'replace'):
                        compare_timestamp = timestamp.replace(tzinfo=None)
                    else:
                        compare_timestamp = timestamp
                    
                    if compare_timestamp in data.index:
                        # Get data up to current timestamp
                        current_data[symbol] = data[data.index <= compare_timestamp]
                
                if current_data:
                    signals = await self.strategy_manager.generate_signals(current_data)
                    
                    # Execute signals
                    for signal in signals:
                        if signal.timestamp == timestamp:  # Only process current signals
                            await self._execute_signal(signal, timestamp, trade_history)
                
                # Record equity curve
                portfolio_summary = self.risk_manager.get_portfolio_summary()
                equity_curve.append({
                    'timestamp': timestamp,
                    'total_value': portfolio_summary['total_value'],
                    'cash': portfolio_summary['cash'],
                    'total_pnl': portfolio_summary['total_pnl'],
                    'total_pnl_pct': portfolio_summary['total_pnl_pct']
                })
            
            # Convert to DataFrame
            if equity_curve:
                equity_df = pd.DataFrame(equity_curve)
                equity_df.set_index('timestamp', inplace=True)
            else:
                # Create empty DataFrame with proper structure
                equity_df = pd.DataFrame(columns=['total_value', 'cash', 'total_pnl', 'total_pnl_pct'])
                equity_df.index.name = 'timestamp'
            
            return equity_df, trade_history
            
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            raise
    
    async def _check_exit_signals(
        self, 
        data_dict: Dict[str, pd.DataFrame], 
        timestamp: datetime, 
        trade_history: List[Dict[str, Any]]
    ):
        """Check for stop loss and take profit exits."""
        for symbol, data in data_dict.items():
            if timestamp in data.index:
                current_price = data.loc[timestamp, 'Close']
                exit_reason = self.risk_manager.check_stop_loss_take_profit(symbol, current_price)
                
                if exit_reason:
                    trade = self.risk_manager.close_position(symbol, current_price, timestamp)
                    if trade:
                        trade['exit_reason'] = exit_reason
                        trade_history.append(trade)
                        logger.info(f"Closed position {symbol} due to {exit_reason}")
    
    async def _execute_signal(
        self, 
        signal, 
        timestamp: datetime, 
        trade_history: List[Dict[str, Any]]
    ):
        """Execute a trading signal."""
        try:
            symbol = signal.symbol
            price = signal.price
            
            # Determine position type
            if signal.signal_type == SignalType.BUY:
                position_type = PositionType.LONG
            elif signal.signal_type == SignalType.SELL:
                position_type = PositionType.SHORT
            else:
                return  # HOLD signal
            
            # Check if we already have a position
            if symbol in self.risk_manager.portfolio.positions:
                # Close existing position
                existing_trade = self.risk_manager.close_position(symbol, price, timestamp)
                if existing_trade:
                    trade_history.append(existing_trade)
            
            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                symbol, 
                price, 
                signal.confidence,
                self.risk_manager.portfolio.total_value
            )
            
            if quantity > 0:
                # Check risk limits
                if self.risk_manager.check_risk_limits(symbol, quantity, price):
                    # Add new position
                    success = self.risk_manager.add_position(
                        symbol, position_type, quantity, price, timestamp
                    )
                    
                    if success:
                        logger.info(f"Executed {signal.signal_type} signal for {symbol}: {quantity} shares @ {price}")
                    else:
                        logger.warning(f"Failed to add position for {symbol}")
                else:
                    logger.warning(f"Risk limits exceeded for {symbol}")
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
    
    def _calculate_performance_metrics(
        self, 
        equity_curve: pd.DataFrame, 
        trade_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        try:
            # Handle empty equity curve
            if equity_curve.empty:
                return {
                    'total_return': 0.0,
                    'total_return_pct': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'max_drawdown_pct': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0
                }
            
            # Basic metrics
            initial_value = equity_curve.iloc[0]['total_value']
            final_value = equity_curve.iloc[-1]['total_value']
            total_return = final_value - initial_value
            total_return_pct = total_return / initial_value
            
            # Calculate returns
            equity_curve['returns'] = equity_curve['total_value'].pct_change()
            
            # Sharpe ratio
            returns = equity_curve['returns'].dropna()
            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0.0
            
            # Maximum drawdown
            equity_curve['cummax'] = equity_curve['total_value'].cummax()
            equity_curve['drawdown'] = (equity_curve['total_value'] - equity_curve['cummax']) / equity_curve['cummax']
            max_drawdown = equity_curve['drawdown'].min()
            max_drawdown_pct = abs(max_drawdown)
            
            # Trade metrics
            if trade_history:
                winning_trades = [t for t in trade_history if t['pnl'] > 0]
                losing_trades = [t for t in trade_history if t['pnl'] < 0]
                
                total_trades = len(trade_history)
                winning_trades_count = len(winning_trades)
                losing_trades_count = len(losing_trades)
                
                win_rate = winning_trades_count / total_trades if total_trades > 0 else 0
                
                avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
                avg_loss = abs(np.mean([t['pnl'] for t in losing_trades])) if losing_trades else 0
                
                profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
                
                best_trade = max([t['pnl'] for t in trade_history]) if trade_history else 0
                worst_trade = min([t['pnl'] for t in trade_history]) if trade_history else 0
            else:
                total_trades = 0
                winning_trades_count = 0
                losing_trades_count = 0
                win_rate = 0
                avg_win = 0
                avg_loss = 0
                profit_factor = 0
                best_trade = 0
                worst_trade = 0
            
            return {
                'total_return': total_return,
                'total_return_pct': total_return_pct,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown_pct,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': total_trades,
                'winning_trades': winning_trades_count,
                'losing_trades': losing_trades_count,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'best_trade': best_trade,
                'worst_trade': worst_trade
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def get_results(self) -> Optional[BacktestResult]:
        """Get backtest results."""
        return self.results
    
    def print_summary(self):
        """Print backtest summary."""
        if not self.results:
            print("No backtest results available")
            return
        
        print("\n" + "="*50)
        print("BACKTEST SUMMARY")
        print("="*50)
        print(f"Total Return: ${self.results.total_return:,.2f} ({self.results.total_return_pct:.2%})")
        print(f"Sharpe Ratio: {self.results.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {self.results.max_drawdown_pct:.2%}")
        print(f"Win Rate: {self.results.win_rate:.2%}")
        print(f"Profit Factor: {self.results.profit_factor:.2f}")
        print(f"Total Trades: {self.results.total_trades}")
        print(f"Winning Trades: {self.results.winning_trades}")
        print(f"Losing Trades: {self.results.losing_trades}")
        print(f"Average Win: ${self.results.avg_win:.2f}")
        print(f"Average Loss: ${self.results.avg_loss:.2f}")
        print(f"Best Trade: ${self.results.best_trade:.2f}")
        print(f"Worst Trade: ${self.results.worst_trade:.2f}")
        print("="*50)


# Global backtest engine instance
backtest_engine = BacktestEngine()


async def get_backtest_engine() -> BacktestEngine:
    """Get the global backtest engine instance."""
    return backtest_engine


if __name__ == "__main__":
    # Test the backtest engine
    async def test():
        engine = BacktestEngine()
        
        # Run backtest
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        symbols = ["AAPL", "MSFT"]
        
        results = await engine.run_backtest(symbols, start_date, end_date)
        engine.print_summary()
    
    asyncio.run(test()) 