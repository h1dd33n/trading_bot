"""
Strategy management module with mean reversion strategy.
All parameters are easily tweakable for optimization.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import structlog
from config import get_settings, StrategyType

logger = structlog.get_logger()


class SignalType(str, Enum):
    """Signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SignalStrength(str, Enum):
    """Signal strength levels."""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass
class Signal:
    """Signal data structure."""
    symbol: str
    timestamp: datetime
    signal_type: SignalType
    strength: SignalStrength
    price: float
    confidence: float
    strategy: str
    metadata: Dict[str, Any]


class BaseStrategy:
    """Base strategy class."""
    
    def __init__(self, settings):
        self.settings = settings
        self.name = "base"
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Generate trading signal."""
        raise NotImplementedError
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate signal confidence."""
        return 0.5


class MeanReversionStrategy(BaseStrategy):
    """Simple mean reversion strategy using moving average."""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.name = "mean_reversion"
    
    def should_trade(self, df: pd.DataFrame, threshold: float = 0.01) -> str:
        """Determine if we should trade based on mean reversion logic."""
        if df.empty or len(df) < self.settings.strategy.lookback_window:
            return "HOLD"
        
        try:
            ma = df['Close'].rolling(window=self.settings.strategy.lookback_window).mean()
            last_price = df['Close'].iloc[-1]
            last_ma = ma.iloc[-1]
            
            if pd.isna(last_ma):
                return "HOLD"
            
            if last_price < last_ma * (1 - threshold):
                return "BUY"
            elif last_price > last_ma * (1 + threshold):
                return "SELL"
            return "HOLD"
            
        except Exception as e:
            logger.error(f"Error in should_trade for {symbol}: {e}")
            return "HOLD"
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Generate mean reversion signal based on moving average."""
        if data.empty or len(data) < self.settings.strategy.lookback_window:
            return None
        
        try:
            # Get latest data point
            latest = data.iloc[-1]
            
            # Calculate moving average
            ma = data['Close'].rolling(window=self.settings.strategy.lookback_window).mean()
            last_ma = ma.iloc[-1]
            
            if pd.isna(last_ma):
                return None
            
            price = latest['Close']
            threshold = self.settings.strategy.threshold
            
            # Generate signal based on mean reversion
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
            
            if price < last_ma * (1 - threshold):
                signal_type = SignalType.BUY
                # Calculate strength based on distance from MA
                distance = (last_ma - price) / last_ma
                if distance > threshold * 2:
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            elif price > last_ma * (1 + threshold):
                signal_type = SignalType.SELL
                # Calculate strength based on distance from MA
                distance = (price - last_ma) / last_ma
                if distance > threshold * 2:
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            
            # Calculate confidence
            confidence = self.calculate_confidence(data)
            
            # Apply confirmation period
            if self._check_confirmation(data, signal_type):
                return Signal(
                    symbol=symbol,
                    timestamp=latest.name,
                    signal_type=signal_type,
                    strength=strength,
                    price=price,
                    confidence=confidence,
                    strategy=self.name,
                    metadata={
                        'moving_average': last_ma,
                        'threshold': threshold,
                        'lookback_window': self.settings.strategy.lookback_window,
                        'price_distance': abs(price - last_ma) / last_ma
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating mean reversion signal for {symbol}: {e}")
            return None
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate signal confidence based on historical accuracy."""
        try:
            if data.empty or len(data) < self.settings.strategy.lookback_window:
                return 0.5
            
            # Calculate moving average
            ma = data['Close'].rolling(window=self.settings.strategy.lookback_window).mean()
            latest_ma = ma.iloc[-1]
            latest_price = data['Close'].iloc[-1]
            
            if pd.isna(latest_ma):
                return 0.5
            
            # Calculate confidence based on distance from moving average
            distance = abs(latest_price - latest_ma) / latest_ma
            threshold = self.settings.strategy.threshold
            
            # Normalize confidence (0-1) based on distance relative to threshold
            confidence = min(distance / threshold, 1.0)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _check_confirmation(self, data: pd.DataFrame, signal_type: SignalType) -> bool:
        """Check if signal is confirmed over multiple periods."""
        confirmation_period = self.settings.strategy.confirmation_period
        
        if len(data) < confirmation_period:
            return False
        
        try:
            # Calculate moving average for recent data
            recent_data = data.tail(confirmation_period)
            ma = recent_data['Close'].rolling(window=self.settings.strategy.lookback_window).mean()
            threshold = self.settings.strategy.threshold
            
            # Check if signal persists over confirmation period
            confirmed_signals = 0
            for i, (timestamp, row) in enumerate(recent_data.iterrows()):
                if i < self.settings.strategy.lookback_window - 1:
                    continue
                
                price = row['Close']
                current_ma = ma.iloc[i]
                
                if pd.isna(current_ma):
                    continue
                
                if signal_type == SignalType.BUY:
                    if price < current_ma * (1 - threshold):
                        confirmed_signals += 1
                elif signal_type == SignalType.SELL:
                    if price > current_ma * (1 + threshold):
                        confirmed_signals += 1
            
            # Require at least 60% of periods to confirm
            min_confirmed = max(1, int(confirmation_period * 0.6))
            return confirmed_signals >= min_confirmed
            
        except Exception as e:
            logger.error(f"Error checking confirmation: {e}")
            return False


class StrategyManager:
    """Manages mean reversion strategy and signal generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.strategies = self._initialize_strategies()
        self.signal_history = []
    
    def _initialize_strategies(self) -> Dict[str, BaseStrategy]:
        """Initialize available strategies."""
        strategies = {
            StrategyType.MEAN_REVERSION: MeanReversionStrategy(self.settings)
        }
        return strategies
    
    async def generate_signals(
        self, 
        data_dict: Dict[str, pd.DataFrame]
    ) -> List[Signal]:
        """Generate signals for all symbols using active strategy."""
        signals = []
        
        try:
            active_strategy = self.strategies.get(self.settings.strategy.strategy_type)
            if not active_strategy:
                logger.error(f"Strategy {self.settings.strategy.strategy_type} not found")
                return signals
            
            for symbol, data in data_dict.items():
                if data.empty:
                    continue
                
                signal = active_strategy.generate_signal(data, symbol)
                if signal:
                    signals.append(signal)
                    self.signal_history.append(signal)
            
            logger.info(f"Generated {len(signals)} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return signals
    
    async def generate_multi_strategy_signals(
        self, 
        data_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[Signal]]:
        """Generate signals using all strategies."""
        all_signals = {}
        
        try:
            for strategy_name, strategy in self.strategies.items():
                signals = []
                
                for symbol, data in data_dict.items():
                    if data.empty:
                        continue
                    
                    signal = strategy.generate_signal(data, symbol)
                    if signal:
                        signals.append(signal)
                
                all_signals[strategy_name] = signals
            
            return all_signals
            
        except Exception as e:
            logger.error(f"Error generating multi-strategy signals: {e}")
            return all_signals
    
    def get_signal_history(self, symbol: Optional[str] = None) -> List[Signal]:
        """Get signal history."""
        if symbol:
            return [s for s in self.signal_history if s.symbol == symbol]
        return self.signal_history
    
    def get_strategy_performance(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Get strategy performance metrics."""
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            recent_signals = [s for s in self.signal_history if s.timestamp >= cutoff_date]
            
            if not recent_signals:
                return {}
            
            # Calculate performance metrics
            total_signals = len(recent_signals)
            buy_signals = len([s for s in recent_signals if s.signal_type == SignalType.BUY])
            sell_signals = len([s for s in recent_signals if s.signal_type == SignalType.SELL])
            
            avg_confidence = np.mean([s.confidence for s in recent_signals])
            
            # Group by strategy
            strategy_stats = {}
            for signal in recent_signals:
                strategy = signal.strategy
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'total': 0,
                        'buy': 0,
                        'sell': 0,
                        'avg_confidence': 0
                    }
                
                strategy_stats[strategy]['total'] += 1
                if signal.signal_type == SignalType.BUY:
                    strategy_stats[strategy]['buy'] += 1
                elif signal.signal_type == SignalType.SELL:
                    strategy_stats[strategy]['sell'] += 1
            
            # Calculate average confidence per strategy
            for strategy in strategy_stats:
                strategy_signals = [s for s in recent_signals if s.strategy == strategy]
                if strategy_signals:
                    strategy_stats[strategy]['avg_confidence'] = np.mean([s.confidence for s in strategy_signals])
            
            return {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'avg_confidence': avg_confidence,
                'strategy_stats': strategy_stats
            }
            
        except Exception as e:
            logger.error(f"Error calculating strategy performance: {e}")
            return {}
    
    def update_strategy_params(self, params: Dict[str, Any]) -> None:
        """Update strategy parameters dynamically."""
        try:
            for key, value in params.items():
                if hasattr(self.settings.strategy, key):
                    setattr(self.settings.strategy, key, value)
                else:
                    logger.warning(f"Invalid strategy parameter: {key}")
            
            logger.info("Strategy parameters updated")
            
        except Exception as e:
            logger.error(f"Error updating strategy parameters: {e}")


# Global strategy manager instance
strategy_manager = StrategyManager()


async def get_strategy_manager() -> StrategyManager:
    """Get the global strategy manager instance."""
    return strategy_manager


if __name__ == "__main__":
    # Test the strategy manager
    async def test():
        from data.data_manager import DataManager
        
        dm = DataManager()
        sm = StrategyManager()
        
        # Fetch data
        data = await dm.fetch_historical_data("EURAUR=X", "1mo", "1h")
        if not data.empty:
            data = await dm.calculate_indicators(data, "EURAUR=X")
            
            # Generate signals
            signals = await sm.generate_signals({"EURAUR=X": data})
            print(f"Generated {len(signals)} signals")
            
            for signal in signals:
                print(f"Signal: {signal.signal_type} {signal.symbol} at {signal.price}")
    
    asyncio.run(test()) 