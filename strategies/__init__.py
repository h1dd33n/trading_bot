"""
Strategy management module for the trading bot.
"""

from .strategy_manager import StrategyManager, get_strategy_manager, Signal, SignalType, SignalStrength

__all__ = ['StrategyManager', 'get_strategy_manager', 'Signal', 'SignalType', 'SignalStrength'] 