"""
MT5 Prop Firm Trading Bot with strict risk management.
Implements 2% daily loss limit and 4% overall loss limit.
Includes yfinance backtesting for validation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import yfinance as yf
from dataclasses import dataclass

# Handle imports for both direct execution and module import
try:
    # Try relative imports first (when run as module)
    from .mt5_config import get_mt5_connection, AccountType, MT5Connection
except ImportError:
    # Fall back to absolute imports (when run directly)
    from mt5_config import get_mt5_connection, AccountType, MT5Connection
from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PropFirmLimits:
    """Prop firm risk limits."""
    max_daily_loss_pct: float = 0.02  # 2%
    max_overall_loss_pct: float = 0.04  # 4%
    max_positions: int = 3
    position_size_pct: float = 0.01  # 1% per trade
    stop_loss_pct: float = 0.015  # 1.5%
    take_profit_pct: float = 0.03  # 3%


class MT5PropFirmBot:
    """MT5 Trading Bot for prop firm accounts with strict risk management."""
    
    def __init__(self):
        self.connection = get_mt5_connection(AccountType.PROP_FIRM)
        self.settings = get_settings()
        self.is_running = False
        self.trading_task = None
        
        # Prop firm specific limits
        self.limits = PropFirmLimits()
        
        # Trading state
        self.positions = []
        self.signals = []
        self.trade_history = []
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.daily_start_balance = 0.0
        self.overall_start_balance = 0.0
        self.max_daily_loss = 0.0
        self.max_overall_loss = 0.0
        
        # Performance tracking
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
    
    async def initialize(self) -> bool:
        """Initialize the prop firm bot with strict risk management."""
        try:
            # Connect to MT5
            self.connection = get_mt5_connection(AccountType.PROP_FIRM)
            if not self.connection.connect():
                logger.error("Failed to connect to MT5")
                return False
            
            # Validate symbols
            available_symbols = self._get_available_symbols()
            logger.info(f"Available symbols: {available_symbols}")
            
            # Filter symbols to only use available ones
            self.connection.config.symbols = [
                symbol for symbol in self.connection.config.symbols 
                if symbol in available_symbols
            ]
            
            if not self.connection.config.symbols:
                logger.error("No valid symbols available for trading")
                return False
            
            logger.info(f"Trading symbols: {self.connection.config.symbols}")
            
            # Initialize tracking
            account_info = self.connection.get_account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return False
            
            self.daily_start_balance = account_info["balance"]
            self.overall_start_balance = account_info["balance"]
            self.last_daily_reset = datetime.now().date()
            
            logger.info("MT5 Prop Firm Bot initialized successfully")
            logger.info(f"Initial balance: ${self.daily_start_balance:,.2f}")
            logger.info(f"Risk limits: {self.limits.max_daily_loss_pct*100}% daily, {self.limits.max_overall_loss_pct*100}% overall")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing prop firm bot: {e}")
            return False
    
    async def start_trading(self):
        """Start the prop firm trading bot."""
        if self.is_running:
            logger.warning("Prop firm bot is already running")
            return
        
        try:
            self.is_running = True
            self.trading_task = asyncio.create_task(self._trading_loop())
            logger.info("MT5 Prop Firm Bot started")
            
        except Exception as e:
            logger.error(f"Error starting prop firm bot: {e}")
            self.is_running = False
    
    async def stop_trading(self):
        """Stop the prop firm trading bot."""
        if not self.is_running:
            logger.warning("Prop firm bot is not running")
            return
        
        try:
            self.is_running = False
            if self.trading_task:
                self.trading_task.cancel()
                try:
                    await self.trading_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("MT5 Prop Firm Bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping prop firm bot: {e}")
    
    async def _trading_loop(self):
        """Main trading loop with strict risk management."""
        while self.is_running:
            try:
                # Check strict risk limits
                risk_check = self._check_strict_risk_limits()
                if not risk_check["within_limits"]:
                    logger.warning("Prop firm risk limits exceeded, stopping trading")
                    await self.stop_trading()
                    break
                
                # Get current positions
                self.positions = self.connection.get_positions()
                
                # Generate signals for each symbol
                for symbol in self.connection.config.symbols:
                    await self._process_symbol(symbol)
                
                # Check for exit signals
                await self._check_exits()
                
                # Update daily tracking
                self._update_daily_tracking()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in prop firm trading loop: {e}")
                await asyncio.sleep(60)
    
    def _check_strict_risk_limits(self) -> Dict[str, Any]:
        """Check strict prop firm risk limits."""
        try:
            account_info = self.connection.get_account_info()
            if account_info is None:
                return {"within_limits": False, "daily_limit_exceeded": True, "overall_limit_exceeded": True}
            
            current_balance = account_info["balance"]
            current_equity = account_info["equity"]
            
            # Calculate daily loss
            daily_loss = self.daily_start_balance - current_equity
            daily_loss_pct = daily_loss / self.daily_start_balance if self.daily_start_balance > 0 else 0
            
            # Calculate overall loss
            overall_loss = self.overall_start_balance - current_equity
            overall_loss_pct = overall_loss / self.overall_start_balance if self.overall_start_balance > 0 else 0
            
            # Check limits
            daily_limit_exceeded = daily_loss_pct > self.limits.max_daily_loss_pct
            overall_limit_exceeded = overall_loss_pct > self.limits.max_overall_loss_pct
            
            return {
                "within_limits": not (daily_limit_exceeded or overall_limit_exceeded),
                "daily_limit_exceeded": daily_limit_exceeded,
                "overall_limit_exceeded": overall_limit_exceeded,
                "daily_loss_pct": daily_loss_pct,
                "overall_loss_pct": overall_loss_pct,
                "daily_loss": daily_loss,
                "overall_loss": overall_loss
            }
            
        except Exception as e:
            logger.error(f"Error checking strict risk limits: {e}")
            return {"within_limits": False, "daily_limit_exceeded": True, "overall_limit_exceeded": True}
    
    async def _process_symbol(self, symbol: str):
        """Process trading signals for a specific symbol with strict risk management."""
        try:
            # Check if we can take more positions
            if len(self.positions) >= self.limits.max_positions:
                logger.info(f"Max positions reached ({self.limits.max_positions}), skipping {symbol}")
                return
            
            # Check if we already have a position in this symbol
            for pos in self.positions:
                if pos["symbol"] == symbol:
                    logger.info(f"Already have position in {symbol}, skipping")
                    return
            
            # Get market data
            rates = self._get_market_data(symbol, timeframe=mt5.TIMEFRAME_H1, count=100)
            if rates is None or len(rates) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return
            
            # Generate signal with stricter criteria
            signal = self._generate_prop_firm_signal(rates, symbol)
            if signal is None:
                logger.info(f"No trading signal for {symbol} - waiting for better conditions")
                return
            
            # Check if we can take the trade
            if self._can_take_prop_firm_trade(signal):
                logger.info(f"Taking trade for {symbol}: {signal['type']} at {signal['price']}")
                await self._execute_prop_firm_signal(signal)
            else:
                logger.info(f"Signal generated for {symbol} but trade conditions not met")
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _get_market_data(self, symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
        """Get market data from MT5 with better error handling."""
        try:
            # First check if symbol is available
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.warning(f"Symbol {symbol} not found in MT5 terminal")
                return None
            
            if not symbol_info.visible:
                # Try to add the symbol
                if not mt5.symbol_select(symbol, True):
                    logger.warning(f"Failed to add symbol {symbol} to Market Watch")
                    return None
            
            # Get rates with retry logic
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No data available for {symbol}")
                return None
            
            if len(rates) < 50:
                logger.warning(f"Insufficient data for {symbol} (got {len(rates)} bars, need at least 50)")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Validate data quality
            if df['close'].isnull().sum() > len(df) * 0.1:  # More than 10% null values
                logger.warning(f"Poor data quality for {symbol} - too many null values")
                return None
            
            logger.info(f"Successfully retrieved {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _generate_prop_firm_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate trading signal with stricter criteria for prop firm."""
        try:
            # Calculate technical indicators
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['rsi'] = self._calculate_rsi(data['close'])
            data['atr'] = self._calculate_atr(data)
            
            # Get latest values
            current_price = data['close'].iloc[-1]
            sma_20 = data['sma_20'].iloc[-1]
            sma_50 = data['sma_50'].iloc[-1]
            rsi = data['rsi'].iloc[-1]
            atr = data['atr'].iloc[-1]
            
            # Log current market conditions
            logger.info(f"{symbol} - Price: {current_price:.5f}, SMA20: {sma_20:.5f}, SMA50: {sma_50:.5f}, RSI: {rsi:.2f}, ATR: {atr:.5f}")
            
            # Check if indicators are valid (not NaN)
            if pd.isna(sma_20) or pd.isna(rsi) or pd.isna(atr):
                logger.warning(f"Invalid indicators for {symbol} - SMA20: {sma_20}, RSI: {rsi}, ATR: {atr}")
                return None
            
            # Stricter signal criteria for prop firm
            signal = None
            
            # Strong oversold condition (RSI < 25 and price significantly below SMA)
            if rsi < 25 and current_price < sma_20 * 0.995:  # 0.5% below SMA
                signal = {
                    "symbol": symbol,
                    "type": "buy",
                    "price": current_price,
                    "strength": 1.0 - (rsi / 25),  # Higher strength for lower RSI
                    "reason": "strong_oversold_prop_firm",
                    "atr": atr
                }
                logger.info(f"BUY signal for {symbol}: RSI={rsi:.2f} (oversold), Price={current_price:.5f} below SMA20={sma_20:.5f}")
            
            # Strong overbought condition (RSI > 75 and price significantly above SMA)
            elif rsi > 75 and current_price > sma_20 * 1.005:  # 0.5% above SMA
                signal = {
                    "symbol": symbol,
                    "type": "sell",
                    "price": current_price,
                    "strength": (rsi - 75) / 25,  # Higher strength for higher RSI
                    "reason": "strong_overbought_prop_firm",
                    "atr": atr
                }
                logger.info(f"SELL signal for {symbol}: RSI={rsi:.2f} (overbought), Price={current_price:.5f} above SMA20={sma_20:.5f}")
            
            if signal is None:
                logger.info(f"No signal for {symbol}: RSI={rsi:.2f}, Price vs SMA20: {((current_price/sma_20)-1)*100:.2f}%")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating prop firm signal for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _can_take_prop_firm_trade(self, signal: Dict[str, Any]) -> bool:
        """Check if we can take the trade based on prop firm risk management."""
        try:
            # Check strict risk limits
            risk_check = self._check_strict_risk_limits()
            if not risk_check["within_limits"]:
                return False
            
            # Check position limits
            if len(self.positions) >= self.limits.max_positions:
                return False
            
            # Check if we already have a position in this symbol
            for pos in self.positions:
                if pos["symbol"] == signal["symbol"]:
                    return False
            
            # Check signal strength (must be strong enough)
            if signal["strength"] < 0.7:  # Minimum 70% strength
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if can take prop firm trade: {e}")
            return False
    
    async def _execute_prop_firm_signal(self, signal: Dict[str, Any]):
        """Execute a trading signal with prop firm risk management."""
        try:
            # Calculate conservative position size
            position_size = self._calculate_prop_firm_position_size(signal)
            if position_size <= 0:
                logger.warning(f"Invalid position size for {signal['symbol']}")
                return
            
            # Prepare order request
            order_type = mt5.ORDER_TYPE_BUY if signal["type"] == "buy" else mt5.ORDER_TYPE_SELL
            price = signal["price"]
            
            # Calculate tight stop loss and take profit
            atr = signal.get("atr", 0.001)
            stop_loss = price - (atr * 1.5) if signal["type"] == "buy" else price + (atr * 1.5)
            take_profit = price + (atr * 3) if signal["type"] == "buy" else price - (atr * 3)
            
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
                "magic": 234001,  # Different magic number for prop firm
                "comment": f"Prop Firm {signal['reason']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Prop firm order failed for {signal['symbol']}: {result.comment}")
                return
            
            # Log successful trade
            logger.info(f"Prop firm order executed: {signal['symbol']} {signal['type']} {position_size} lots")
            
            # Add to trade history
            self.trade_history.append({
                "time": datetime.now(),
                "symbol": signal["symbol"],
                "type": signal["type"],
                "volume": position_size,
                "price": price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "reason": signal["reason"],
                "strength": signal["strength"]
            })
            
        except Exception as e:
            logger.error(f"Error executing prop firm signal: {e}")
    
    def _calculate_prop_firm_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate conservative position size for prop firm."""
        try:
            # Get account info
            account_info = self.connection.get_account_info()
            if account_info is None:
                return 0.0
            
            balance = account_info["balance"]
            atr = signal.get("atr", 0.001)
            
            # Calculate risk amount (1% of balance)
            risk_amount = balance * self.limits.position_size_pct
            
            # Calculate position size based on ATR and stop loss
            stop_loss_atr = 1.5  # 1.5 ATR stop loss
            position_size = risk_amount / (stop_loss_atr * atr)
            
            # Ensure very conservative position sizes
            min_size = 0.01  # Minimum 0.01 lot
            max_size = balance * 0.05 / atr  # Maximum 5% of balance
            
            position_size = max(min_size, min(position_size, max_size))
            
            return round(position_size, 2)
            
        except Exception as e:
            logger.error(f"Error calculating prop firm position size: {e}")
            return 0.0
    
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
                if self._should_exit_prop_firm_position(position, current_price):
                    await self._close_prop_firm_position(position)
                    
        except Exception as e:
            logger.error(f"Error checking prop firm exits: {e}")
    
    def _should_exit_prop_firm_position(self, position: Dict[str, Any], current_price: float) -> bool:
        """Check if prop firm position should be closed."""
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
            logger.error(f"Error checking prop firm exit conditions: {e}")
            return False
    
    async def _close_prop_firm_position(self, position: Dict[str, Any]):
        """Close a prop firm position."""
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
                "magic": 234001,
                "comment": "Prop Firm close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Prop firm close order failed for {position['symbol']}: {result.comment}")
                return
            
            logger.info(f"Prop firm position closed: {position['symbol']} {position['volume']} lots")
            
        except Exception as e:
            logger.error(f"Error closing prop firm position: {e}")
    
    def _update_daily_tracking(self):
        """Update daily tracking for prop firm limits."""
        try:
            account_info = self.connection.get_account_info()
            if account_info is None:
                return
            
            self.daily_pnl = account_info["profit"]
            
            # Reset daily tracking at market open (simplified)
            current_time = datetime.now()
            if current_time.hour == 0 and current_time.minute == 0:
                self.daily_start_balance = account_info["balance"]
                logger.info("Daily tracking reset")
            
        except Exception as e:
            logger.error(f"Error updating daily tracking: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current prop firm bot status."""
        try:
            account_info = self.connection.get_account_info()
            risk_check = self._check_strict_risk_limits()
            
            return {
                "account_type": "prop_firm",
                "is_running": self.is_running,
                "connected": self.connection.connected,
                "account_info": account_info,
                "positions": self.positions,
                "risk_limits": risk_check,
                "daily_pnl": self.daily_pnl,
                "trade_count": len(self.trade_history),
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "total_pnl": self.total_pnl
            }
            
        except Exception as e:
            logger.error(f"Error getting prop firm status: {e}")
            return {"error": str(e)}
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed bot status including waiting status."""
        try:
            account_info = self.connection.get_account_info()
            risk_check = self._check_strict_risk_limits()
            
            # Get current market conditions for each symbol
            market_conditions = {}
            for symbol in self.connection.config.symbols:
                try:
                    rates = self._get_market_data(symbol, timeframe=mt5.TIMEFRAME_H1, count=100)
                    if rates is not None and len(rates) >= 50:
                        # Calculate indicators
                        rates['sma_20'] = rates['close'].rolling(window=20).mean()
                        rates['rsi'] = self._calculate_rsi(rates['close'])
                        rates['atr'] = self._calculate_atr(rates)
                        
                        current_price = rates['close'].iloc[-1]
                        sma_20 = rates['sma_20'].iloc[-1]
                        rsi = rates['rsi'].iloc[-1]
                        atr = rates['atr'].iloc[-1]
                        
                        market_conditions[symbol] = {
                            "current_price": current_price,
                            "sma_20": sma_20,
                            "rsi": rsi,
                            "atr": atr,
                            "price_vs_sma": ((current_price/sma_20)-1)*100 if not pd.isna(sma_20) else None,
                            "signal_ready": rsi < 25 or rsi > 75
                        }
                except Exception as e:
                    market_conditions[symbol] = {"error": str(e)}
            
            return {
                "account_type": "prop_firm",
                "is_running": self.is_running,
                "connected": self.connection.connected,
                "account_info": account_info,
                "positions": self.positions,
                "risk_limits": risk_check,
                "market_conditions": market_conditions,
                "waiting_for_trades": len(self.positions) < self.limits.max_positions,
                "can_take_trades": risk_check.get("within_limits", False),
                "trade_count": len(self.trade_history),
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "total_pnl": self.total_pnl
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed status: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.connection.connected:
                self.connection.disconnect()
        except Exception as e:
            logger.error(f"Error during prop firm cleanup: {e}")

    def _get_available_symbols(self) -> List[str]:
        """Get list of available symbols in MT5 terminal."""
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                logger.warning("Failed to get symbols from MT5")
                return []
            
            # Filter for forex symbols
            forex_symbols = []
            for symbol in symbols:
                symbol_name = symbol.name
                # Common forex pairs
                if any(pair in symbol_name for pair in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]):
                    forex_symbols.append(symbol_name)
            
            logger.info(f"Found {len(forex_symbols)} forex symbols")
            return forex_symbols
            
        except Exception as e:
            logger.error(f"Error getting available symbols: {e}")
            return []


class YFinanceBacktester:
    """YFinance backtester for prop firm strategy validation."""
    
    def __init__(self, symbols: List[str], initial_capital: float = 100000):
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.limits = PropFirmLimits()
    
    def run_backtest(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run backtest with prop firm risk management."""
        try:
            results = {}
            
            for symbol in self.symbols:
                # Download data
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval="1h")
                
                if data.empty:
                    logger.warning(f"No data for {symbol}")
                    continue
                
                # Run backtest for this symbol
                symbol_result = self._backtest_symbol(data, symbol)
                results[symbol] = symbol_result
            
            # Aggregate results
            total_result = self._aggregate_results(results)
            
            return {
                "symbol_results": results,
                "total_result": total_result,
                "backtest_period": f"{start_date} to {end_date}",
                "initial_capital": self.initial_capital
            }
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {"error": str(e)}
    
    def _backtest_symbol(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Backtest a single symbol with prop firm rules."""
        try:
            # Calculate indicators
            data['sma_20'] = data['Close'].rolling(window=20).mean()
            data['rsi'] = self._calculate_rsi(data['Close'])
            data['atr'] = self._calculate_atr(data)
            
            # Initialize tracking
            capital = self.initial_capital
            positions = []
            trades = []
            daily_pnl = 0
            max_daily_loss = capital * self.limits.max_daily_loss_pct
            max_overall_loss = capital * self.limits.max_overall_loss_pct
            
            for i in range(50, len(data)):  # Start after enough data for indicators
                current_data = data.iloc[:i+1]
                current_price = current_data['Close'].iloc[-1]
                
                # Check risk limits
                if daily_pnl < -max_daily_loss or (capital - self.initial_capital) < -max_overall_loss:
                    break
                
                # Generate signal
                signal = self._generate_backtest_signal(current_data, symbol)
                
                # Execute trades
                if signal:
                    # Check if we can take trade
                    if len(positions) < self.limits.max_positions:
                        # Calculate position size
                        position_size = self._calculate_backtest_position_size(
                            signal, capital, current_data['atr'].iloc[-1]
                        )
                        
                        if position_size > 0:
                            # Execute trade
                            trade = {
                                "time": current_data.index[-1],
                                "symbol": symbol,
                                "type": signal["type"],
                                "price": current_price,
                                "volume": position_size,
                                "stop_loss": signal["stop_loss"],
                                "take_profit": signal["take_profit"]
                            }
                            
                            positions.append(trade)
                            trades.append(trade)
                
                # Check existing positions for exits
                positions = self._check_backtest_exits(positions, current_price, trades)
                
                # Update daily P&L
                if i % 24 == 0:  # Reset daily P&L every 24 hours
                    daily_pnl = 0
            
            # Calculate final results
            total_pnl = sum(trade.get("pnl", 0) for trade in trades)
            win_rate = len([t for t in trades if t.get("pnl", 0) > 0]) / len(trades) if trades else 0
            
            return {
                "total_trades": len(trades),
                "winning_trades": len([t for t in trades if t.get("pnl", 0) > 0]),
                "losing_trades": len([t for t in trades if t.get("pnl", 0) < 0]),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "final_capital": capital + total_pnl,
                "return_pct": (total_pnl / self.initial_capital) * 100
            }
            
        except Exception as e:
            logger.error(f"Error backtesting {symbol}: {e}")
            return {"error": str(e)}
    
    def _generate_backtest_signal(self, data: pd.DataFrame, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate signal for backtesting."""
        try:
            current_price = data['Close'].iloc[-1]
            sma_20 = data['sma_20'].iloc[-1]
            rsi = data['rsi'].iloc[-1]
            atr = data['atr'].iloc[-1]
            
            # Same signal logic as prop firm bot
            if rsi < 25 and current_price < sma_20 * 0.995:
                stop_loss = current_price - (atr * 1.5)
                take_profit = current_price + (atr * 3)
                return {
                    "type": "buy",
                    "price": current_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            elif rsi > 75 and current_price > sma_20 * 1.005:
                stop_loss = current_price + (atr * 1.5)
                take_profit = current_price - (atr * 3)
                return {
                    "type": "sell",
                    "price": current_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating backtest signal: {e}")
            return None
    
    def _calculate_backtest_position_size(self, signal: Dict[str, Any], capital: float, atr: float) -> float:
        """Calculate position size for backtesting."""
        try:
            risk_amount = capital * self.limits.position_size_pct
            stop_loss_atr = 1.5
            position_size = risk_amount / (stop_loss_atr * atr)
            
            min_size = 0.01
            max_size = capital * 0.05 / atr
            
            return max(min_size, min(position_size, max_size))
            
        except Exception as e:
            logger.error(f"Error calculating backtest position size: {e}")
            return 0.0
    
    def _check_backtest_exits(self, positions: List[Dict], current_price: float, trades: List[Dict]) -> List[Dict]:
        """Check for exits in backtesting."""
        remaining_positions = []
        
        for position in positions:
            should_exit = False
            
            # Check stop loss
            if position["type"] == "buy" and current_price <= position["stop_loss"]:
                should_exit = True
            elif position["type"] == "sell" and current_price >= position["stop_loss"]:
                should_exit = True
            
            # Check take profit
            elif position["type"] == "buy" and current_price >= position["take_profit"]:
                should_exit = True
            elif position["type"] == "sell" and current_price <= position["take_profit"]:
                should_exit = True
            
            if should_exit:
                # Calculate P&L
                if position["type"] == "buy":
                    pnl = (current_price - position["price"]) * position["volume"]
                else:
                    pnl = (position["price"] - current_price) * position["volume"]
                
                position["pnl"] = pnl
                trades.append(position)
            else:
                remaining_positions.append(position)
        
        return remaining_positions
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _aggregate_results(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Aggregate backtest results across all symbols."""
        try:
            total_trades = sum(r.get("total_trades", 0) for r in results.values())
            total_pnl = sum(r.get("total_pnl", 0) for r in results.values())
            total_wins = sum(r.get("winning_trades", 0) for r in results.values())
            
            overall_win_rate = total_wins / total_trades if total_trades > 0 else 0
            overall_return = (total_pnl / self.initial_capital) * 100
            
            # Calculate additional metrics
            total_losses = total_trades - total_wins
            avg_win = total_pnl / total_wins if total_wins > 0 else 0
            avg_loss = total_pnl / total_losses if total_losses > 0 else 0
            
            return {
                "total_trades": total_trades,
                "total_pnl": total_pnl,
                "winning_trades": total_wins,
                "losing_trades": total_losses,
                "overall_win_rate": overall_win_rate,
                "overall_return_pct": overall_return,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            }
            
        except Exception as e:
            logger.error(f"Error aggregating results: {e}")
            return {"error": str(e)}


# Example usage
async def main():
    """Example usage of MT5 Prop Firm Bot."""
    bot = MT5PropFirmBot()
    
    try:
        # Initialize bot
        if await bot.initialize():
            print("Prop firm bot initialized successfully")
            
            # Run backtest first
            backtester = YFinanceBacktester(
                symbols=["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"],
                initial_capital=100000
            )
            
            backtest_result = backtester.run_backtest(
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
            
            print("Backtest results:", backtest_result)
            
            # Start live trading
            await bot.start_trading()
            
            # Run for some time
            await asyncio.sleep(3600)  # Run for 1 hour
            
            # Stop trading
            await bot.stop_trading()
            
        else:
            print("Failed to initialize prop firm bot")
            
    except KeyboardInterrupt:
        print("Stopping prop firm bot...")
        await bot.stop_trading()
    finally:
        bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 