"""
MT5 Trading Bot for regular accounts.
Uses pip sizes for position sizing and includes proper risk management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Handle imports for both direct execution and module import
try:
    # Try relative imports first (when run as module)
    from .mt5_config import get_mt5_connection, AccountType, MT5Connection
except ImportError:
    # Fall back to absolute imports (when run directly)
    from mt5_config import get_mt5_connection, AccountType, MT5Connection

# Handle config import
try:
    from config import get_settings
except ImportError:
    # Fall back to parent directory import
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_settings

logger = logging.getLogger(__name__)


class MT5TradingBot:
    """MT5 Trading Bot for regular accounts."""
    
    def __init__(self, account_type: AccountType = AccountType.REGULAR):
        self.account_type = account_type
        self.connection = get_mt5_connection(account_type)
        self.settings = get_settings()
        self.is_running = False
        self.trading_task = None
        
        # Trading state
        self.positions = []
        self.signals = []
        self.trade_history = []
        
        # Risk management
        self.daily_pnl = 0.0
        self.max_daily_loss = 0.0
        self.max_overall_loss = 0.0
    
    async def initialize(self) -> bool:
        """Initialize the trading bot."""
        try:
            # Connect to MT5
            if not self.connection.connect():
                logger.error("Failed to connect to MT5")
                return False
            
            # Get account info and set risk limits
            account_info = self.connection.get_account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
            
            balance = account_info["balance"]
            self.max_daily_loss = balance * self.connection.config.max_daily_loss_pct
            self.max_overall_loss = balance * self.connection.config.max_overall_loss_pct
            
            logger.info(f"MT5 Trading Bot initialized for {self.account_type.value} account")
            logger.info(f"Account balance: {balance}")
            logger.info(f"Max daily loss: {self.max_daily_loss}")
            logger.info(f"Max overall loss: {self.max_overall_loss}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MT5 trading bot: {e}")
            return False
    
    async def start_trading(self):
        """Start the trading bot."""
        if self.is_running:
            logger.warning("Trading bot is already running")
            return
        
        try:
            self.is_running = True
            self.trading_task = asyncio.create_task(self._trading_loop())
            logger.info("MT5 Trading Bot started")
            
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            self.is_running = False
    
    async def stop_trading(self):
        """Stop the trading bot."""
        if not self.is_running:
            logger.warning("Trading bot is not running")
            return
        
        try:
            self.is_running = False
            if self.trading_task:
                self.trading_task.cancel()
                try:
                    await self.trading_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("MT5 Trading Bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
    
    async def _trading_loop(self):
        """Main trading loop."""
        while self.is_running:
            try:
                # Check risk limits
                risk_check = self.connection.check_risk_limits()
                if not risk_check["within_limits"]:
                    logger.warning("Risk limits exceeded, stopping trading")
                    await self.stop_trading()
                    break
                
                # Get current positions
                self.positions = self.connection.get_positions()
                
                # Generate signals for each symbol
                for symbol in self.connection.config.symbols:
                    await self._process_symbol(symbol)
                
                # Check for exit signals
                await self._check_exits()
                
                # Update daily P&L
                self._update_daily_pnl()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    async def _process_symbol(self, symbol: str):
        """Process trading signals for a specific symbol."""
        try:
            # Get market data
            rates = self._get_market_data(symbol, timeframe=mt5.TIMEFRAME_H1, count=100)
            if rates is None or len(rates) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return
            
            # Generate signal
            signal = self._generate_signal(rates, symbol)
            if signal is None:
                return
            
            # Check if we can take the trade
            if self._can_take_trade(signal):
                await self._execute_signal(signal)
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _get_market_data(self, symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
        """Get market data from MT5."""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _generate_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate trading signal using mean reversion strategy."""
        try:
            # Calculate technical indicators
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['rsi'] = self._calculate_rsi(data['close'])
            
            # Get latest values
            current_price = data['close'].iloc[-1]
            sma_20 = data['sma_20'].iloc[-1]
            sma_50 = data['sma_50'].iloc[-1]
            rsi = data['rsi'].iloc[-1]
            
            # Check for mean reversion signal
            signal = None
            
            # Oversold condition (RSI < 30 and price below SMA)
            if rsi < 30 and current_price < sma_20:
                signal = {
                    "symbol": symbol,
                    "type": "buy",
                    "price": current_price,
                    "strength": 1.0 - (rsi / 30),  # Higher strength for lower RSI
                    "reason": "oversold_mean_reversion"
                }
            
            # Overbought condition (RSI > 70 and price above SMA)
            elif rsi > 70 and current_price > sma_20:
                signal = {
                    "symbol": symbol,
                    "type": "sell",
                    "price": current_price,
                    "strength": (rsi - 70) / 30,  # Higher strength for higher RSI
                    "reason": "overbought_mean_reversion"
                }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _can_take_trade(self, signal: Dict[str, Any]) -> bool:
        """Check if we can take the trade based on risk management."""
        try:
            # Check if we have too many positions
            if len(self.positions) >= self.connection.config.max_positions:
                return False
            
            # Check if we already have a position in this symbol
            for pos in self.positions:
                if pos["symbol"] == signal["symbol"]:
                    return False
            
            # Check risk limits
            risk_check = self.connection.check_risk_limits()
            if not risk_check["within_limits"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if can take trade: {e}")
            return False
    
    async def _execute_signal(self, signal: Dict[str, Any]):
        """Execute a trading signal."""
        try:
            # Calculate position size based on pip value
            position_size = self._calculate_position_size(signal)
            if position_size <= 0:
                logger.warning(f"Invalid position size for {signal['symbol']}")
                return
            
            # Prepare order request
            order_type = mt5.ORDER_TYPE_BUY if signal["type"] == "buy" else mt5.ORDER_TYPE_SELL
            price = signal["price"]
            
            # Calculate stop loss and take profit
            pip_value = self._get_pip_value(signal["symbol"])
            stop_loss = price - (pip_value * 20) if signal["type"] == "buy" else price + (pip_value * 20)
            take_profit = price + (pip_value * 40) if signal["type"] == "buy" else price - (pip_value * 40)
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal["symbol"],
                "volume": position_size,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 234000,
                "comment": f"MT5 Bot {signal['reason']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed for {signal['symbol']}: {result.comment}")
                return
            
            # Log successful trade
            logger.info(f"Order executed: {signal['symbol']} {signal['type']} {position_size} lots")
            
            # Add to trade history
            self.trade_history.append({
                "time": datetime.now(),
                "symbol": signal["symbol"],
                "type": signal["type"],
                "volume": position_size,
                "price": price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "reason": signal["reason"]
            })
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
    
    def _calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate position size based on pip value and risk management."""
        try:
            # Get account info
            account_info = self.connection.get_account_info()
            if account_info is None:
                return 0.0
            
            balance = account_info["balance"]
            pip_value = self._get_pip_value(signal["symbol"])
            
            # Calculate risk amount (2% of balance)
            risk_amount = balance * self.connection.config.position_size_pct
            
            # Calculate position size based on pip value and stop loss
            stop_loss_pips = 20  # 20 pips stop loss
            position_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Ensure minimum and maximum position sizes
            min_size = 0.01  # Minimum 0.01 lot
            max_size = balance * 0.1 / pip_value  # Maximum 10% of balance
            
            position_size = max(min_size, min(position_size, max_size))
            
            return round(position_size, 2)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def _get_pip_value(self, symbol: str) -> float:
        """Get pip value for a symbol."""
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return 0.0001  # Default pip value
            
            # Calculate pip value based on symbol properties
            if symbol_info.digits == 3 or symbol_info.digits == 5:
                # JPY pairs
                pip_value = 0.01
            else:
                # Other pairs
                pip_value = 0.0001
            
            return pip_value
            
        except Exception as e:
            logger.error(f"Error getting pip value for {symbol}: {e}")
            return 0.0001
    
    async def _check_exits(self):
        """Check for exit signals on existing positions."""
        try:
            for position in self.positions:
                # Get current market data
                rates = self._get_market_data(position["symbol"], mt5.TIMEFRAME_H1, count=10)
                if rates is None:
                    continue
                
                current_price = rates['close'].iloc[-1]
                
                # Check if stop loss or take profit hit
                if self._should_exit_position(position, current_price):
                    await self._close_position(position)
                    
        except Exception as e:
            logger.error(f"Error checking exits: {e}")
    
    def _should_exit_position(self, position: Dict[str, Any], current_price: float) -> bool:
        """Check if position should be closed."""
        try:
            # Check stop loss
            if position["type"] == "buy" and current_price <= position.get("stop_loss", 0):
                return True
            elif position["type"] == "sell" and current_price >= position.get("stop_loss", float('inf')):
                return True
            
            # Check take profit
            if position["type"] == "buy" and current_price >= position.get("take_profit", float('inf')):
                return True
            elif position["type"] == "sell" and current_price <= position.get("take_profit", 0):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
            return False
    
    async def _close_position(self, position: Dict[str, Any]):
        """Close a position."""
        try:
            # Prepare close request
            order_type = mt5.ORDER_TYPE_SELL if position["type"] == "buy" else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position["symbol"],
                "volume": position["volume"],
                "type": order_type,
                "position": position["ticket"],
                "price": position["price_current"],
                "deviation": 20,
                "magic": 234000,
                "comment": "MT5 Bot close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close order failed for {position['symbol']}: {result.comment}")
                return
            
            logger.info(f"Position closed: {position['symbol']} {position['volume']} lots")
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    def _update_daily_pnl(self):
        """Update daily P&L tracking."""
        try:
            account_info = self.connection.get_account_info()
            if account_info is None:
                return
            
            self.daily_pnl = account_info["profit"]
            
        except Exception as e:
            logger.error(f"Error updating daily P&L: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        try:
            account_info = self.connection.get_account_info()
            risk_check = self.connection.check_risk_limits()
            
            return {
                "account_type": self.account_type.value,
                "is_running": self.is_running,
                "connected": self.connection.connected,
                "account_info": account_info,
                "positions": self.positions,
                "risk_limits": risk_check,
                "daily_pnl": self.daily_pnl,
                "trade_count": len(self.trade_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.connection.connected:
                self.connection.disconnect()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Example usage
async def main():
    """Example usage of MT5 Trading Bot."""
    bot = MT5TradingBot(AccountType.REGULAR)
    
    try:
        # Initialize bot
        if await bot.initialize():
            print("Bot initialized successfully")
            
            # Start trading
            await bot.start_trading()
            
            # Run for some time
            await asyncio.sleep(3600)  # Run for 1 hour
            
            # Stop trading
            await bot.stop_trading()
            
        else:
            print("Failed to initialize bot")
            
    except KeyboardInterrupt:
        print("Stopping bot...")
        await bot.stop_trading()
    finally:
        bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 