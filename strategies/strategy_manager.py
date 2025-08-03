"""
Strategy management module with multiple mean reversion strategies.
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
    """Mean reversion strategy using z-score."""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.name = "mean_reversion"
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Generate mean reversion signal based on z-score."""
        if data.empty or len(data) < self.settings.strategy.lookback_window:
            return None
        
        try:
            # Get latest data point
            latest = data.iloc[-1]
            
            # Check if we have enough data for indicators
            if pd.isna(latest['z_score']):
                return None
            
            z_score = latest['z_score']
            z_threshold = self.settings.strategy.z_score_threshold
            price = latest['Close']
            
            # Generate signal based on z-score
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
            
            if z_score > z_threshold:
                signal_type = SignalType.SELL
                if z_score > z_threshold * 1.5:
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            elif z_score < -z_threshold:
                signal_type = SignalType.BUY
                if z_score < -z_threshold * 1.5:
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
                        'z_score': z_score,
                        'threshold': z_threshold,
                        'lookback_window': self.settings.strategy.lookback_window
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating mean reversion signal for {symbol}: {e}")
            return None
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate signal confidence based on historical accuracy."""
        try:
            # Simple confidence based on z-score magnitude
            latest_z = data.iloc[-1]['z_score']
            if pd.isna(latest_z):
                return 0.5
            
            # Normalize z-score to confidence (0-1)
            confidence = min(abs(latest_z) / (self.settings.strategy.z_score_threshold * 2), 1.0)
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _check_confirmation(self, data: pd.DataFrame, signal_type: SignalType) -> bool:
        """Check if signal is confirmed over multiple periods."""
        confirmation_period = self.settings.strategy.confirmation_period
        
        if len(data) < confirmation_period:
            return False
        
        # Check if signal persists over confirmation period
        recent_data = data.tail(confirmation_period)
        z_scores = recent_data['z_score'].dropna()
        
        if len(z_scores) < confirmation_period:
            return False
        
        if signal_type == SignalType.BUY:
            return all(z < -self.settings.strategy.z_score_threshold * 0.8 for z in z_scores)
        elif signal_type == SignalType.SELL:
            return all(z > self.settings.strategy.z_score_threshold * 0.8 for z in z_scores)
        
        return False


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands mean reversion strategy."""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.name = "bollinger_bands"
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Generate Bollinger Bands signal."""
        if data.empty or len(data) < self.settings.strategy.bollinger_period:
            return None
        
        try:
            latest = data.iloc[-1]
            
            if pd.isna(latest['bollinger_upper']) or pd.isna(latest['bollinger_lower']):
                return None
            
            price = latest['Close']
            upper_band = latest['bollinger_upper']
            lower_band = latest['bollinger_lower']
            middle_band = latest['bollinger_middle']
            
            # Calculate percentage distance from bands
            upper_distance = (price - upper_band) / upper_band
            lower_distance = (price - lower_band) / lower_band
            
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
            
            # Generate signals
            if price <= lower_band:
                signal_type = SignalType.BUY
                if lower_distance < -0.02:  # 2% below lower band
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            elif price >= upper_band:
                signal_type = SignalType.SELL
                if upper_distance > 0.02:  # 2% above upper band
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            
            # Calculate confidence
            confidence = self.calculate_confidence(data)
            
            # Check confirmation
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
                        'upper_band': upper_band,
                        'lower_band': lower_band,
                        'middle_band': middle_band,
                        'upper_distance': upper_distance,
                        'lower_distance': lower_distance
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating Bollinger Bands signal for {symbol}: {e}")
            return None
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate confidence based on band width and position."""
        try:
            latest = data.iloc[-1]
            
            if pd.isna(latest['bollinger_upper']) or pd.isna(latest['bollinger_lower']):
                return 0.5
            
            # Calculate band width
            band_width = (latest['bollinger_upper'] - latest['bollinger_lower']) / latest['bollinger_middle']
            
            # Normalize confidence based on band width (wider bands = higher confidence)
            confidence = min(band_width * 10, 1.0)
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger confidence: {e}")
            return 0.5
    
    def _check_confirmation(self, data: pd.DataFrame, signal_type: SignalType) -> bool:
        """Check Bollinger Bands confirmation."""
        confirmation_period = self.settings.strategy.confirmation_period
        
        if len(data) < confirmation_period:
            return False
        
        recent_data = data.tail(confirmation_period)
        
        if signal_type == SignalType.BUY:
            return all(row['Close'] <= row['bollinger_lower'] for _, row in recent_data.iterrows() 
                      if not pd.isna(row['bollinger_lower']))
        elif signal_type == SignalType.SELL:
            return all(row['Close'] >= row['bollinger_upper'] for _, row in recent_data.iterrows() 
                      if not pd.isna(row['bollinger_upper']))
        
        return False


class RSIMeanReversionStrategy(BaseStrategy):
    """RSI-based mean reversion strategy."""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.name = "rsi_mean_reversion"
    
    def generate_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Generate RSI mean reversion signal."""
        if data.empty or len(data) < self.settings.strategy.rsi_period:
            return None
        
        # Check if RSI column exists
        if 'rsi' not in data.columns:
            logger.error(f"RSI column missing from data for {symbol}. Available columns: {data.columns.tolist()}")
            return None
        
        try:
            latest = data.iloc[-1]
            
            if pd.isna(latest['rsi']):
                return None
            
            rsi = latest['rsi']
            price = latest['Close']
            
            oversold = self.settings.strategy.rsi_oversold
            overbought = self.settings.strategy.rsi_overbought
            
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
            
            # Generate signals
            if rsi <= oversold:
                signal_type = SignalType.BUY
                if rsi <= oversold * 0.8:  # Very oversold
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            elif rsi >= overbought:
                signal_type = SignalType.SELL
                if rsi >= overbought * 1.2:  # Very overbought
                    strength = SignalStrength.STRONG
                else:
                    strength = SignalStrength.MEDIUM
            
            # Calculate confidence
            confidence = self.calculate_confidence(data)
            
            # Check confirmation
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
                        'rsi': rsi,
                        'oversold_threshold': oversold,
                        'overbought_threshold': overbought
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating RSI signal for {symbol}: {e}")
            # Add more detailed error information
            if 'rsi' not in data.columns:
                logger.error(f"RSI column missing from data. Available columns: {data.columns.tolist()}")
            return None
    
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        """Calculate RSI confidence."""
        try:
            latest = data.iloc[-1]
            
            if pd.isna(latest['rsi']):
                return 0.5
            
            rsi = latest['rsi']
            oversold = self.settings.strategy.rsi_oversold
            overbought = self.settings.strategy.rsi_overbought
            
            # Calculate confidence based on RSI extremes
            if rsi <= oversold:
                confidence = (oversold - rsi) / oversold
            elif rsi >= overbought:
                confidence = (rsi - overbought) / (100 - overbought)
            else:
                confidence = 0.5
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating RSI confidence: {e}")
            return 0.5
    
    def _check_confirmation(self, data: pd.DataFrame, signal_type: SignalType) -> bool:
        """Check RSI confirmation."""
        confirmation_period = self.settings.strategy.confirmation_period
        
        if len(data) < confirmation_period:
            return False
        
        recent_data = data.tail(confirmation_period)
        rsi_values = recent_data['rsi'].dropna()
        
        if len(rsi_values) < confirmation_period:
            return False
        
        oversold = self.settings.strategy.rsi_oversold
        overbought = self.settings.strategy.rsi_overbought
        
        if signal_type == SignalType.BUY:
            return all(rsi <= oversold * 1.1 for rsi in rsi_values)
        elif signal_type == SignalType.SELL:
            return all(rsi >= overbought * 0.9 for rsi in rsi_values)
        
        return False


class StrategyManager:
    """Manages multiple strategies and signal generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.strategies = self._initialize_strategies()
        self.signal_history = []
    
    def _initialize_strategies(self) -> Dict[str, BaseStrategy]:
        """Initialize available strategies."""
        strategies = {
            StrategyType.MEAN_REVERSION: MeanReversionStrategy(self.settings),
            StrategyType.BOLLINGER_BANDS: BollingerBandsStrategy(self.settings),
            StrategyType.RSI_MEAN_REVERSION: RSIMeanReversionStrategy(self.settings)
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
        data = await dm.fetch_historical_data("AAPL", "1mo", "1h")
        if not data.empty:
            data = await dm.calculate_indicators(data, "AAPL")
            
            # Generate signals
            signals = await sm.generate_signals({"AAPL": data})
            print(f"Generated {len(signals)} signals")
            
            for signal in signals:
                print(f"Signal: {signal.signal_type} {signal.symbol} at {signal.price}")
    
    asyncio.run(test()) 