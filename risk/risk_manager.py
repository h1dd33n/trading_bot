"""
Risk management module with position sizing, portfolio constraints, and dynamic risk adjustment.
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
from config import get_settings

logger = structlog.get_logger()


class PositionType(str, Enum):
    """Position types."""
    LONG = "long"
    SHORT = "short"


class RiskLevel(str, Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Position:
    """Position data structure."""
    symbol: str
    position_type: PositionType
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    stop_loss: float
    take_profit: float


@dataclass
class Portfolio:
    """Portfolio data structure."""
    total_value: float
    cash: float
    positions: Dict[str, Position]
    total_pnl: float
    total_pnl_pct: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float


class RiskManager:
    """Comprehensive risk management system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.portfolio = Portfolio(
            total_value=100000.0,  # Starting capital
            cash=100000.0,
            positions={},
            total_pnl=0.0,
            total_pnl_pct=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            volatility=0.0
        )
        self.trade_history = []
        self.performance_history = []
    
    def calculate_position_size(
        self, 
        symbol: str, 
        price: float, 
        signal_confidence: float,
        portfolio_value: float
    ) -> float:
        """Calculate position size based on risk parameters and Kelly criterion."""
        try:
            # Base position size as percentage of portfolio
            base_size_pct = self.settings.strategy.position_size_pct
            
            # Adjust for signal confidence
            confidence_multiplier = signal_confidence
            
            # Apply Kelly criterion if enabled
            if self.settings.risk.kelly_criterion:
                kelly_fraction = self._calculate_kelly_fraction(symbol)
                base_size_pct *= kelly_fraction * self.settings.risk.kelly_fraction
            
            # Apply dynamic risk adjustment
            if self.settings.strategy.enable_dynamic_risk:
                risk_multiplier = self._calculate_risk_multiplier()
                base_size_pct *= risk_multiplier
            
            # Calculate position size in dollars
            position_value = portfolio_value * base_size_pct * confidence_multiplier
            
            # Apply portfolio constraints
            position_value = self._apply_portfolio_constraints(symbol, position_value, portfolio_value)
            
            # Convert to quantity
            quantity = position_value / price
            
            logger.info(f"Calculated position size for {symbol}: {quantity:.2f} shares (${position_value:.2f})")
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0.0
    
    def _calculate_kelly_fraction(self, symbol: str) -> float:
        """Calculate Kelly criterion fraction based on historical performance."""
        try:
            # Get historical trades for this symbol
            symbol_trades = [t for t in self.trade_history if t['symbol'] == symbol]
            
            if len(symbol_trades) < 10:  # Need minimum trades for Kelly
                return 0.5
            
            # Calculate win rate and average win/loss
            wins = [t for t in symbol_trades if t['pnl'] > 0]
            losses = [t for t in symbol_trades if t['pnl'] < 0]
            
            if not wins or not losses:
                return 0.5
            
            win_rate = len(wins) / len(symbol_trades)
            avg_win = np.mean([t['pnl'] for t in wins])
            avg_loss = abs(np.mean([t['pnl'] for t in losses]))
            
            if avg_loss == 0:
                return 0.5
            
            # Kelly formula: f = (bp - q) / b
            # where b = odds received, p = win probability, q = loss probability
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            
            # Clamp to reasonable range
            return max(0.1, min(0.9, kelly_fraction))
            
        except Exception as e:
            logger.error(f"Error calculating Kelly fraction: {e}")
            return 0.5
    
    def _calculate_risk_multiplier(self) -> float:
        """Calculate dynamic risk multiplier based on performance."""
        try:
            if len(self.performance_history) < self.settings.strategy.performance_lookback:
                return self.settings.strategy.risk_multiplier
            
            # Get recent performance
            recent_performance = self.performance_history[-self.settings.strategy.performance_lookback:]
            
            # Calculate Sharpe ratio
            returns = [p['return'] for p in recent_performance]
            if not returns:
                return self.settings.strategy.risk_multiplier
            
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return self.settings.strategy.risk_multiplier
            
            sharpe_ratio = avg_return / std_return
            
            # Adjust risk multiplier based on Sharpe ratio
            if sharpe_ratio > self.settings.strategy.sharpe_threshold:
                # Good performance - increase risk
                risk_multiplier = min(
                    self.settings.strategy.max_risk_multiplier,
                    self.settings.strategy.risk_multiplier * 1.1
                )
            elif sharpe_ratio < 0:
                # Poor performance - decrease risk
                risk_multiplier = max(
                    self.settings.strategy.min_risk_multiplier,
                    self.settings.strategy.risk_multiplier * 0.9
                )
            else:
                risk_multiplier = self.settings.strategy.risk_multiplier
            
            return risk_multiplier
            
        except Exception as e:
            logger.error(f"Error calculating risk multiplier: {e}")
            return self.settings.strategy.risk_multiplier
    
    def _apply_portfolio_constraints(
        self, 
        symbol: str, 
        position_value: float, 
        portfolio_value: float
    ) -> float:
        """Apply portfolio-level constraints."""
        try:
            # Maximum position size
            max_position_pct = self.settings.strategy.position_size_pct * 2
            max_position_value = portfolio_value * max_position_pct
            position_value = min(position_value, max_position_value)
            
            # Maximum portfolio risk per trade
            max_risk_value = portfolio_value * self.settings.risk.max_portfolio_risk
            position_value = min(position_value, max_risk_value)
            
            # Maximum number of positions
            if len(self.portfolio.positions) >= self.settings.strategy.max_positions:
                position_value = 0
            
            # Minimum cash reserve
            required_cash = portfolio_value * self.settings.risk.min_cash_reserve
            available_cash = self.portfolio.cash - required_cash
            position_value = min(position_value, available_cash)
            
            return max(0, position_value)
            
        except Exception as e:
            logger.error(f"Error applying portfolio constraints: {e}")
            return 0.0
    
    def calculate_stop_loss_take_profit(
        self, 
        entry_price: float, 
        position_type: PositionType
    ) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels."""
        try:
            stop_loss_pct = self.settings.strategy.stop_loss_pct
            take_profit_pct = self.settings.strategy.take_profit_pct
            
            if position_type == PositionType.LONG:
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
            else:  # SHORT
                stop_loss = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 - take_profit_pct)
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating stop loss/take profit: {e}")
            return entry_price, entry_price
    
    def check_risk_limits(self, symbol: str, quantity: float, price: float) -> bool:
        """Check if trade meets risk limits."""
        try:
            # Check maximum drawdown
            if self.portfolio.max_drawdown > self.settings.strategy.max_drawdown_pct:
                logger.warning(f"Maximum drawdown limit exceeded: {self.portfolio.max_drawdown:.2%}")
                return False
            
            # Check correlation with existing positions
            if not self._check_correlation_limits(symbol):
                logger.warning(f"Correlation limit exceeded for {symbol}")
                return False
            
            # Check sector exposure
            if not self._check_sector_exposure(symbol):
                logger.warning(f"Sector exposure limit exceeded for {symbol}")
                return False
            
            # Check leverage limits
            total_exposure = sum(abs(p.quantity * p.current_price) for p in self.portfolio.positions.values())
            leverage = total_exposure / self.portfolio.total_value
            
            if leverage > self.settings.risk.max_leverage:
                logger.warning(f"Leverage limit exceeded: {leverage:.2f}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return False
    
    def _check_correlation_limits(self, symbol: str) -> bool:
        """Check correlation with existing positions."""
        try:
            if len(self.portfolio.positions) < 2:
                return True
            
            # Simple correlation check (in real implementation, would use actual price data)
            # For now, assume high correlation for same sector stocks
            correlation_threshold = self.settings.risk.correlation_threshold
            
            # This is a simplified check - in practice, you'd calculate actual correlations
            return True
            
        except Exception as e:
            logger.error(f"Error checking correlation limits: {e}")
            return True
    
    def _check_sector_exposure(self, symbol: str) -> bool:
        """Check sector exposure limits."""
        try:
            # Simplified sector check - in practice, you'd have sector mapping
            max_sector_exposure = self.settings.risk.max_sector_exposure
            
            # For now, assume all tech stocks are in same sector
            tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            if symbol in tech_symbols:
                tech_exposure = sum(
                    p.quantity * p.current_price 
                    for p in self.portfolio.positions.values() 
                    if p.symbol in tech_symbols
                ) / self.portfolio.total_value
                
                if tech_exposure > max_sector_exposure:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking sector exposure: {e}")
            return True
    
    def update_portfolio(self, symbol: str, price: float, timestamp: datetime):
        """Update portfolio with current prices."""
        try:
            # Update existing positions
            for position in self.portfolio.positions.values():
                if position.symbol == symbol:
                    position.current_price = price
                    position.unrealized_pnl = (price - position.entry_price) * position.quantity
                    position.unrealized_pnl_pct = position.unrealized_pnl / (position.entry_price * position.quantity)
            
            # Calculate portfolio metrics
            self._calculate_portfolio_metrics(timestamp)
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    def _calculate_portfolio_metrics(self, timestamp: datetime):
        """Calculate portfolio performance metrics."""
        try:
            # Calculate total position value
            position_value = sum(
                p.quantity * p.current_price for p in self.portfolio.positions.values()
            )
            
            # Update portfolio
            self.portfolio.total_value = self.portfolio.cash + position_value
            self.portfolio.total_pnl = sum(p.unrealized_pnl for p in self.portfolio.positions.values())
            self.portfolio.total_pnl_pct = self.portfolio.total_pnl / (self.portfolio.total_value - self.portfolio.total_pnl)
            
            # Calculate volatility
            if len(self.performance_history) > 1:
                returns = [p['return'] for p in self.performance_history]
                self.portfolio.volatility = np.std(returns) if returns else 0.0
            
            # Calculate Sharpe ratio
            if self.portfolio.volatility > 0:
                self.portfolio.sharpe_ratio = self.portfolio.total_pnl_pct / self.portfolio.volatility
            else:
                self.portfolio.sharpe_ratio = 0.0
            
            # Update max drawdown
            if self.portfolio.total_pnl_pct < self.portfolio.max_drawdown:
                self.portfolio.max_drawdown = self.portfolio.total_pnl_pct
            
            # Store performance history
            self.performance_history.append({
                'timestamp': timestamp,
                'total_value': self.portfolio.total_value,
                'return': self.portfolio.total_pnl_pct
            })
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
    
    def add_position(
        self, 
        symbol: str, 
        position_type: PositionType, 
        quantity: float, 
        price: float,
        timestamp: datetime
    ) -> bool:
        """Add a new position to the portfolio."""
        try:
            # Calculate stop loss and take profit
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(price, position_type)
            
            # Create position
            position = Position(
                symbol=symbol,
                position_type=position_type,
                quantity=quantity,
                entry_price=price,
                entry_time=timestamp,
                current_price=price,
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Update portfolio
            self.portfolio.positions[symbol] = position
            self.portfolio.cash -= quantity * price
            
            logger.info(f"Added position: {symbol} {position_type} {quantity} @ {price}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return False
    
    def close_position(self, symbol: str, price: float, timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Close a position and return trade details."""
        try:
            if symbol not in self.portfolio.positions:
                return None
            
            position = self.portfolio.positions[symbol]
            
            # Calculate realized P&L
            if position.position_type == PositionType.LONG:
                realized_pnl = (price - position.entry_price) * position.quantity
            else:  # SHORT
                realized_pnl = (position.entry_price - price) * position.quantity
            
            # Update portfolio
            self.portfolio.cash += position.quantity * price
            del self.portfolio.positions[symbol]
            
            # Record trade
            trade = {
                'symbol': symbol,
                'position_type': position.position_type,
                'entry_price': position.entry_price,
                'exit_price': price,
                'quantity': position.quantity,
                'entry_time': position.entry_time,
                'exit_time': timestamp,
                'pnl': realized_pnl,
                'pnl_pct': realized_pnl / (position.entry_price * position.quantity)
            }
            
            self.trade_history.append(trade)
            
            logger.info(f"Closed position: {symbol} P&L: ${realized_pnl:.2f}")
            return trade
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return None
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Optional[str]:
        """Check if position should be closed due to stop loss or take profit."""
        try:
            if symbol not in self.portfolio.positions:
                return None
            
            position = self.portfolio.positions[symbol]
            
            if position.position_type == PositionType.LONG:
                if current_price <= position.stop_loss:
                    return "stop_loss"
                elif current_price >= position.take_profit:
                    return "take_profit"
            else:  # SHORT
                if current_price >= position.stop_loss:
                    return "stop_loss"
                elif current_price <= position.take_profit:
                    return "take_profit"
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking stop loss/take profit: {e}")
            return None
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        try:
            return {
                'total_value': self.portfolio.total_value,
                'cash': self.portfolio.cash,
                'total_pnl': self.portfolio.total_pnl,
                'total_pnl_pct': self.portfolio.total_pnl_pct,
                'max_drawdown': self.portfolio.max_drawdown,
                'sharpe_ratio': self.portfolio.sharpe_ratio,
                'volatility': self.portfolio.volatility,
                'num_positions': len(self.portfolio.positions),
                'positions': [
                    {
                        'symbol': p.symbol,
                        'type': p.position_type,
                        'quantity': p.quantity,
                        'entry_price': p.entry_price,
                        'current_price': p.current_price,
                        'unrealized_pnl': p.unrealized_pnl,
                        'unrealized_pnl_pct': p.unrealized_pnl_pct
                    }
                    for p in self.portfolio.positions.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}
    
    def get_trade_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trade history."""
        if symbol:
            return [t for t in self.trade_history if t['symbol'] == symbol]
        return self.trade_history


# Global risk manager instance
risk_manager = RiskManager()


async def get_risk_manager() -> RiskManager:
    """Get the global risk manager instance."""
    return risk_manager


if __name__ == "__main__":
    # Test the risk manager
    async def test():
        rm = RiskManager()
        
        # Test position sizing
        quantity = rm.calculate_position_size("AAPL", 150.0, 0.8, 100000.0)
        print(f"Position size: {quantity:.2f} shares")
        
        # Test adding position
        success = rm.add_position("AAPL", PositionType.LONG, quantity, 150.0, datetime.now())
        print(f"Added position: {success}")
        
        # Test portfolio update
        rm.update_portfolio("AAPL", 155.0, datetime.now())
        summary = rm.get_portfolio_summary()
        print(f"Portfolio P&L: ${summary['total_pnl']:.2f}")
    
    asyncio.run(test()) 