"""
Backtesting module for the trading bot.
"""

from .backtest_engine import BacktestEngine, get_backtest_engine, BacktestResult

__all__ = ['BacktestEngine', 'get_backtest_engine', 'BacktestResult'] 