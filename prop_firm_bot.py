#!/usr/bin/env python3
"""
Prop Firm Trading Bot
Uses the exact same strategy as single_test.py but with configurable risk parameters.
Supports both backtesting and live trading on MT5.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import structlog
import yfinance as yf
from pathlib import Path
import json
import MetaTrader5 as mt5

logger = structlog.get_logger()

@dataclass
class PropFirmConfig:
    """Configuration for prop firm bot with same strategy as single_test.py."""
    
    # Account credentials
    server: str = "ACGMarkets-Main"
    login: str = "2194718"
    password: str = "vUD&V86dwc"
    
    # Trading symbols (backtest vs live)
    backtest_symbols: List[str] = None  # For backtesting (with =X)
    live_symbols: List[str] = None      # For live trading (with .pro)
    
    # Strategy parameters (same as single_test.py)
    lookback_window: int = 30
    threshold: float = 0.01  # 1% deviation from SMA
    position_size_pct: float = 0.02  # 2% of capital per trade
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    
    # Risk management (configurable for prop firm)
    max_loss_per_trade: float = 0.01  # 1% max loss per trade
    max_daily_loss: float = 0.02  # 2% max daily loss
    max_overall_loss: float = 0.04  # 4% max overall loss
    max_positions: int = 10
    
    # Leverage settings (same as single_test.py)
    base_leverage: float = 1.0
    max_leverage: float = 5.0
    risk_compounding: bool = True
    enable_dynamic_leverage: bool = True
    winning_streak_threshold: int = 3
    losing_streak_threshold: int = 2
    
    # Risk compounding settings
    profit_multiplier_cap: float = 2.0
    
    # Margin call thresholds
    margin_call_threshold_50: float = 0.5
    margin_call_threshold_80: float = 0.8
    extreme_value_threshold: float = 10.0
    safety_balance_threshold: float = 5.0
    
    # Live trading settings
    enable_live_trading: bool = False
    demo_account: bool = True
    
    def __post_init__(self):
        if self.backtest_symbols is None:
            self.backtest_symbols = ["EURAUD=X", "EURCAD=X"]
        if self.live_symbols is None:
            self.live_symbols = ["EURAUD.pro", "EURCAD.pro"]

@dataclass
class PropFirmResult:
    """Result of prop firm backtest."""
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


class PropFirmBot:
    """Prop Firm Trading Bot using exact same strategy as single_test.py."""
    
    def __init__(self, config: Optional[PropFirmConfig] = None):
        self.config = config or PropFirmConfig()
        
        # Trading state
        self.winning_streak = 0
        self.losing_streak = 0
        self.current_leverage = self.config.base_leverage
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.positions = {}
        
        # MT5 connection
        self.mt5_connected = False
        
    def connect_mt5(self) -> bool:
        """Connect to MT5 terminal."""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login to account
            if not mt5.login(
                login=int(self.config.login),
                password=self.config.password,
                server=self.config.server
            ):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                mt5.shutdown()
                return False
            
            logger.info(f"Connected to MT5: {account_info.server}")
            logger.info(f"Account: {account_info.login}, Balance: ${account_info.balance:.2f}")
            logger.info(f"Equity: ${account_info.equity:.2f}, Margin: ${account_info.margin:.2f}")
            
            self.mt5_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect_mt5(self):
        """Disconnect from MT5 terminal."""
        if self.mt5_connected:
            mt5.shutdown()
            self.mt5_connected = False
            logger.info("Disconnected from MT5")
    
    def get_available_symbols(self) -> List[str]:
        """Get available symbols from MT5."""
        if not self.mt5_connected:
            return []
        
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
            
            symbol_names = [symbol.name for symbol in symbols]
            logger.info(f"Available symbols: {symbol_names[:10]}...")  # Show first 10
            return symbol_names
            
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information from MT5."""
        if not self.mt5_connected:
            return None
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            return {
                'name': symbol_info.name,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'trade_mode': symbol_info.trade_mode,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info:
            return (symbol_info['bid'] + symbol_info['ask']) / 2
        return None
    
    def place_order(self, symbol: str, order_type: str, volume: float, 
                   price: float, sl: float, tp: float) -> Optional[int]:
        """Place order on MT5."""
        if not self.mt5_connected:
            return None
        
        try:
            # Convert order type
            if order_type == "BUY":
                mt5_order_type = mt5.ORDER_TYPE_BUY
            elif order_type == "SELL":
                mt5_order_type = mt5.ORDER_TYPE_SELL
            else:
                logger.error(f"Invalid order type: {order_type}")
                return None
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": "prop_firm_bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
            
            logger.info(f"Order placed: {symbol} {order_type} {volume} @ {price}")
            return result.order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get current positions from MT5."""
        if not self.mt5_connected:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            return [
                {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'time': pos.time
                }
                for pos in positions
            ]
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def run_backtest(
        self,
        timeframe: str = "1y",
        interval: str = "1d",
        initial_balance: float = 100000.0
    ) -> PropFirmResult:
        """Run backtest using exact same logic as single_test.py."""
        
        print(f"🧪 Prop Firm Bot Backtest")
        print(f"📊 Symbols: {self.config.backtest_symbols}")
        print(f"📅 Timeframe: {timeframe}, Interval: {interval}")
        print("=" * 60)
        
        # Print current parameters
        print(f"\n⚙️ Current Parameters:")
        print(f"   Initial Balance: ${initial_balance:,.2f}")
        print(f"   Lookback Window: {self.config.lookback_window}")
        print(f"   Threshold: {self.config.threshold:.3f} ({self.config.threshold*100:.1f}%)")
        print(f"   Position Size: {self.config.position_size_pct:.3f} ({self.config.position_size_pct*100:.1f}%)")
        print(f"   Stop Loss: {self.config.stop_loss_pct:.3f} ({self.config.stop_loss_pct*100:.1f}%)")
        print(f"   Take Profit: {self.config.take_profit_pct:.3f} ({self.config.take_profit_pct*100:.1f}%)")
        print(f"   Max Loss Per Trade: {self.config.max_loss_per_trade:.3f} ({self.config.max_loss_per_trade*100:.1f}%)")
        print(f"   Max Daily Loss: {self.config.max_daily_loss:.3f} ({self.config.max_daily_loss*100:.1f}%)")
        print(f"   Max Overall Loss: {self.config.max_overall_loss:.3f} ({self.config.max_overall_loss*100:.1f}%)")
        print(f"   Base Leverage: 1:{self.config.base_leverage}")
        print(f"   Max Leverage: 1:{self.config.max_leverage}")
        print(f"   Risk Compounding: {'Enabled' if self.config.risk_compounding else 'Disabled'}")
        print(f"   Dynamic Leverage: Based on win/loss streaks")
        
        try:
            # Fetch data for all symbols
            all_data = {}
            for symbol in self.config.backtest_symbols:
                print(f"\n📈 Fetching data for {symbol}...")
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=timeframe, interval=interval)
                if not data.empty:
                    all_data[symbol] = data
                    print(f"   ✅ {symbol}: {len(data)} data points from {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
                else:
                    print(f"   ❌ {symbol}: No data available")
            
            if not all_data:
                print("❌ No data available for any symbol")
                return None
            
            # Run backtest simulation (exact same logic as single_test.py)
            result = await self._run_backtest_simulation(all_data, initial_balance)
            
            if result:
                self._print_detailed_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prop firm backtest: {e}")
            print(f"❌ Error: {e}")
            return None
    
    async def _run_backtest_simulation(self, all_data: Dict[str, pd.DataFrame], initial_balance: float = 100000.0) -> PropFirmResult:
        """Run backtest simulation using exact same logic as single_test.py."""
        
        # Simulate trading (same as single_test.py)
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
        print(f"   Base Leverage: 1:{self.config.base_leverage}")
        print(f"   Max Leverage: 1:{self.config.max_leverage}")
        print(f"   Effective Capital: ${initial_balance * self.config.max_leverage:,.2f}")
        print(f"   Risk Compounding: {'Enabled' if self.config.risk_compounding else 'Disabled'}")
        print(f"   Dynamic Leverage: Win/Loss streak based")
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
                        # Check for invalid values
                        if np.isnan(unrealized_pnl) or np.isinf(unrealized_pnl):
                            unrealized_pnl = 0.0
                        position['unrealized_pnl'] = unrealized_pnl
                        
                        # Check stop loss / take profit (same as single_test.py)
                        if self._should_exit_position(position, current_price):
                            # Close position
                            exit_price = current_price
                            pnl = (exit_price - position['entry_price']) * position['quantity']
                            # Check for invalid values
                            if np.isnan(pnl) or np.isinf(pnl):
                                pnl = 0.0
                            portfolio_value += pnl
                            
                            trades.append({
                                'symbol': symbol,
                                'entry_date': position['entry_date'],
                                'exit_date': date,
                                'entry_price': position['entry_price'],
                                'exit_price': exit_price,
                                'quantity': position['quantity'],
                                'pnl': pnl,
                                'pnl_pct': pnl / (position['entry_price'] * position['quantity']) if (position['entry_price'] * position['quantity']) != 0 else 0.0
                            })
                            
                            # Update streaks and dynamic leverage (same as single_test.py)
                            self._update_streaks_and_leverage(pnl)
                            
                            del positions[symbol]
            
            # Generate signals for new positions (same as single_test.py)
            for symbol, data in all_data.items():
                if date in data.index and symbol not in positions:
                    # Get data up to current date
                    historical_data = data.loc[:date]
                    if len(historical_data) >= self.config.lookback_window:
                        signal = self._generate_signal(historical_data)
                        
                        if signal in ['BUY', 'SELL']:
                            # Calculate position size with dynamic leverage (same as single_test.py)
                            base_position_size = portfolio_value * self.config.position_size_pct
                            leveraged_position_size = base_position_size * self.current_leverage
                            quantity = leveraged_position_size / current_price
                            
                            # Apply risk compounding if enabled (same as single_test.py)
                            if self.config.risk_compounding and portfolio_value > initial_balance:
                                # Increase position size based on accumulated profits
                                profit_multiplier = min(portfolio_value / initial_balance, self.config.profit_multiplier_cap)
                                quantity *= profit_multiplier
                            
                            # Check for invalid values and reasonable bounds
                            if (np.isnan(quantity) or np.isinf(quantity) or quantity <= 0 or 
                                quantity * current_price > portfolio_value * 0.5):  # Max 50% of portfolio per position
                                continue  # Skip this trade
                            
                            # Open position
                            positions[symbol] = {
                                'entry_date': date,
                                'entry_price': current_price,
                                'quantity': quantity,
                                'type': signal,
                                'unrealized_pnl': 0,
                                'leverage_applied': self.current_leverage,
                                'risk_compounding': self.config.risk_compounding,
                                'winning_streak': self.winning_streak,
                                'losing_streak': self.losing_streak
                            }
            
            # Record equity curve
            total_value = portfolio_value
            for position in positions.values():
                if not np.isnan(position['unrealized_pnl']) and not np.isinf(position['unrealized_pnl']):
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
                # Check for invalid values
                if np.isnan(pnl) or np.isinf(pnl):
                    pnl = 0.0
                portfolio_value += pnl
                
                trades.append({
                    'symbol': symbol,
                    'entry_date': position['entry_date'],
                    'exit_date': timeline[-1],
                    'entry_price': position['entry_price'],
                    'exit_price': last_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'pnl_pct': pnl / (position['entry_price'] * position['quantity']) if (position['entry_price'] * position['quantity']) != 0 else 0.0
                })
        
        # Calculate final balance with leverage effects (same as single_test.py)
        final_balance = portfolio_value
        for position in positions.values():
            if not np.isnan(position['unrealized_pnl']) and not np.isinf(position['unrealized_pnl']):
                if position['type'] == 'BUY':
                    final_balance += position['unrealized_pnl']
                else:  # SELL position
                    final_balance -= position['unrealized_pnl']
        
        # Apply leverage risk (same as single_test.py)
        leverage_risk_factor = 1.0
        if final_balance < initial_balance * self.config.margin_call_threshold_50:
            leverage_risk_factor = 0.5
        elif final_balance < initial_balance * self.config.margin_call_threshold_80:
            leverage_risk_factor = 0.8
        
        # Additional safety check for extreme values
        if abs(final_balance) > initial_balance * self.config.extreme_value_threshold:
            final_balance = initial_balance
            leverage_risk_factor = 0.1
        
        # Calculate metrics
        return self._calculate_metrics(
            trades, equity_curve, initial_balance, final_balance, leverage_risk_factor
        )
    
    async def run_live_trading(self):
        """Run live trading on MT5."""
        print("🚀 Starting Prop Firm Live Trading")
        print("=" * 60)
        
        # Connect to MT5
        if not self.connect_mt5():
            print("❌ Failed to connect to MT5")
            return
        
        try:
            # Get available symbols
            available_symbols = self.get_available_symbols()
            print(f"📊 Available symbols: {len(available_symbols)}")
            
            # Check if our symbols are available
            for symbol in self.config.live_symbols:
                if symbol in available_symbols:
                    print(f"✅ {symbol} is available")
                else:
                    print(f"❌ {symbol} is NOT available")
            
            print(f"\n📈 Live Trading Symbols: {', '.join(self.config.live_symbols)}")
            print(f"📊 Backtest Symbols: {', '.join(self.config.backtest_symbols)}")
            
            # Get account info
            account_info = mt5.account_info()
            initial_balance = account_info.balance
            print(f"\n💰 Account Balance: ${initial_balance:,.2f}")
            print(f"📈 Current Equity: ${account_info.equity:,.2f}")
            
            # Start trading loop
            print(f"\n🔄 Starting trading loop...")
            print("Press Ctrl+C to stop")
            
            while True:
                try:
                    # Get current positions
                    positions = self.get_positions()
                    current_symbols = [pos['symbol'] for pos in positions]
                    
                    # Check each symbol for signals
                    for symbol in self.config.live_symbols:
                        try:
                            if symbol not in current_symbols:  # No position in this symbol
                                # Get historical data for signal generation
                                data = await self._get_mt5_data(symbol, self.config.lookback_window + 10)
                                if data is not None and len(data) >= self.config.lookback_window:
                                    signal = self._generate_signal(data)
                                    
                                    if signal in ['BUY', 'SELL']:
                                        # Get current price
                                        current_price = self.get_current_price(symbol)
                                        if current_price is None:
                                            logger.warning(f"Could not get current price for {symbol}")
                                            continue
                                        
                                        # Calculate position size
                                        account_info = mt5.account_info()
                                        base_position_size = account_info.equity * self.config.position_size_pct
                                        leveraged_position_size = base_position_size * self.current_leverage
                                        
                                        # Get symbol info for volume calculation
                                        symbol_info = self.get_symbol_info(symbol)
                                        if symbol_info is None:
                                            logger.warning(f"Could not get symbol info for {symbol}")
                                            continue
                                        
                                        # Calculate volume (convert to lots)
                                        volume = leveraged_position_size / current_price
                                        volume = round(volume / symbol_info['volume_step']) * symbol_info['volume_step']
                                        volume = max(volume, symbol_info['volume_min'])
                                        volume = min(volume, symbol_info['volume_max'])
                                        
                                        if volume < symbol_info['volume_min']:
                                            logger.warning(f"Volume too small for {symbol}: {volume}")
                                            continue
                                        
                                        # Calculate stop loss and take profit
                                        if signal == "BUY":
                                            sl = current_price * (1 - self.config.stop_loss_pct)
                                            tp = current_price * (1 + self.config.take_profit_pct)
                                        else:  # SELL
                                            sl = current_price * (1 + self.config.stop_loss_pct)
                                            tp = current_price * (1 - self.config.take_profit_pct)
                                        
                                        # Place order
                                        order_ticket = self.place_order(
                                            symbol, signal, volume, current_price, sl, tp
                                        )
                                        
                                        if order_ticket:
                                            print(f"✅ {signal} order placed for {symbol}: {volume} lots @ {current_price}")
                                            print(f"   SL: {sl:.5f}, TP: {tp:.5f}")
                                else:
                                    logger.warning(f"Insufficient data for {symbol}: {len(data) if data is not None else 0} points")
                            else:
                                logger.info(f"Already have position in {symbol}")
                        except Exception as e:
                            logger.error(f"Error processing {symbol}: {e}")
                            continue
                    
                    # Wait before next iteration
                    await asyncio.sleep(60)  # Check every minute
                    
                except KeyboardInterrupt:
                    print("\n🛑 Trading stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    await asyncio.sleep(60)
        
        finally:
            self.disconnect_mt5()
    
    async def _get_mt5_data(self, symbol: str, count: int) -> Optional[pd.DataFrame]:
        """Get historical data from MT5."""
        if not self.mt5_connected:
            return None
        
        try:
            # Get rates from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No data received for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            
            # Check if we have the required columns
            required_columns = ['time', 'open', 'high', 'low', 'close', 'tick_volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required columns for {symbol}. Available: {df.columns.tolist()}")
                return None
            
            # Rename 'close' to 'Close' to match our expected format
            df = df.rename(columns={'close': 'Close'})
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            logger.info(f"Retrieved {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting MT5 data for {symbol}: {e}")
            return None
    
    def save_config(self, config_file: str = "prop_firm_config.json"):
        """Save configuration to file."""
        config_dict = {
            'server': self.config.server,
            'login': self.config.login,
            'password': '*' * len(self.config.password),  # Mask password
            'backtest_symbols': self.config.backtest_symbols,
            'live_symbols': self.config.live_symbols,
            'lookback_window': self.config.lookback_window,
            'threshold': self.config.threshold,
            'position_size_pct': self.config.position_size_pct,
            'stop_loss_pct': self.config.stop_loss_pct,
            'take_profit_pct': self.config.take_profit_pct,
            'max_loss_per_trade': self.config.max_loss_per_trade,
            'max_daily_loss': self.config.max_daily_loss,
            'max_overall_loss': self.config.max_overall_loss,
            'max_positions': self.config.max_positions,
            'base_leverage': self.config.base_leverage,
            'max_leverage': self.config.max_leverage,
            'risk_compounding': self.config.risk_compounding,
            'enable_dynamic_leverage': self.config.enable_dynamic_leverage,
            'winning_streak_threshold': self.config.winning_streak_threshold,
            'losing_streak_threshold': self.config.losing_streak_threshold,
            'profit_multiplier_cap': self.config.profit_multiplier_cap,
            'margin_call_threshold_50': self.config.margin_call_threshold_50,
            'margin_call_threshold_80': self.config.margin_call_threshold_80,
            'extreme_value_threshold': self.config.extreme_value_threshold,
            'safety_balance_threshold': self.config.safety_balance_threshold,
            'enable_live_trading': self.config.enable_live_trading,
            'demo_account': self.config.demo_account
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def load_config(self, config_file: str = "prop_firm_config.json"):
        """Load configuration from file."""
        if Path(config_file).exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update config with loaded data
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def update_config(self, **kwargs):
        """Update configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown parameter: {key}")
    
    def display_config(self):
        """Display current configuration."""
        print(f"\n{'='*60}")
        print("PROP FIRM BOT CONFIGURATION")
        print(f"{'='*60}")
        
        print(f"\n🔐 Account Credentials:")
        print(f"   Server: {self.config.server}")
        print(f"   Login: {self.config.login}")
        print(f"   Password: {'*' * len(self.config.password)}")
        
        print(f"\n📊 Trading Symbols:")
        print(f"   Backtest Symbols: {', '.join(self.config.backtest_symbols)}")
        print(f"   Live Symbols: {', '.join(self.config.live_symbols)}")
        
        print(f"\n📈 Strategy Parameters (same as single_test.py):")
        print(f"   Lookback Window: {self.config.lookback_window}")
        print(f"   Threshold: {self.config.threshold:.3f} ({self.config.threshold*100:.1f}%)")
        print(f"   Position Size: {self.config.position_size_pct:.3f} ({self.config.position_size_pct*100:.1f}%)")
        print(f"   Stop Loss: {self.config.stop_loss_pct:.3f} ({self.config.stop_loss_pct*100:.1f}%)")
        print(f"   Take Profit: {self.config.take_profit_pct:.3f} ({self.config.take_profit_pct*100:.1f}%)")
        
        print(f"\n🛡️ Risk Management (Configurable):")
        print(f"   Max Loss Per Trade: {self.config.max_loss_per_trade:.3f} ({self.config.max_loss_per_trade*100:.1f}%)")
        print(f"   Max Daily Loss: {self.config.max_daily_loss:.3f} ({self.config.max_daily_loss*100:.1f}%)")
        print(f"   Max Overall Loss: {self.config.max_overall_loss:.3f} ({self.config.max_overall_loss*100:.1f}%)")
        print(f"   Max Positions: {self.config.max_positions}")
        
        print(f"\n⚙️ Leverage Settings (same as single_test.py):")
        print(f"   Base Leverage: 1:{self.config.base_leverage}")
        print(f"   Max Leverage: 1:{self.config.max_leverage}")
        print(f"   Risk Compounding: {'Enabled' if self.config.risk_compounding else 'Disabled'}")
        print(f"   Dynamic Leverage: {'Enabled' if self.config.enable_dynamic_leverage else 'Disabled'}")
        print(f"   Winning Streak Threshold: {self.config.winning_streak_threshold}")
        print(f"   Losing Streak Threshold: {self.config.losing_streak_threshold}")
        
        print(f"\n🚀 Live Trading Settings:")
        print(f"   Enable Live Trading: {'Yes' if self.config.enable_live_trading else 'No'}")
        print(f"   Demo Account: {'Yes' if self.config.demo_account else 'No'}")
        
        print(f"\n{'='*60}")
    
    def _generate_signal(self, data: pd.DataFrame) -> str:
        """Generate trading signal using exact same logic as single_test.py."""
        if data.empty or len(data) < self.config.lookback_window:
            return "HOLD"
        
        try:
            ma = data['Close'].rolling(window=self.config.lookback_window).mean()
            last_price = data['Close'].iloc[-1]
            last_ma = ma.iloc[-1]
            
            if pd.isna(last_ma):
                return "HOLD"
            
            threshold = self.config.threshold
            
            if last_price < last_ma * (1 - threshold):
                return "BUY"
            elif last_price > last_ma * (1 + threshold):
                return "SELL"
            return "HOLD"
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return "HOLD"
    
    def _should_exit_position(self, position: Dict, current_price: float) -> bool:
        """Check if position should be closed due to stop loss or take profit (same as single_test.py)."""
        entry_price = position['entry_price']
        position_type = position['type']
        
        if position_type == 'BUY':
            stop_loss = entry_price * (1 - self.config.stop_loss_pct)
            take_profit = entry_price * (1 + self.config.take_profit_pct)
            
            return current_price <= stop_loss or current_price >= take_profit
        
        elif position_type == 'SELL':
            stop_loss = entry_price * (1 + self.config.stop_loss_pct)
            take_profit = entry_price * (1 - self.config.take_profit_pct)
            
            return current_price >= stop_loss or current_price <= take_profit
        
        return False
    
    def _update_streaks_and_leverage(self, pnl: float):
        """Update winning/losing streaks and adjust leverage accordingly (same as single_test.py)."""
        
        if pnl > 0:  # Winning trade
            self.winning_streak += 1
            self.losing_streak = 0  # Reset losing streak
            
            # Increase leverage based on winning streak
            if (self.config.enable_dynamic_leverage and 
                self.winning_streak >= self.config.winning_streak_threshold):
                leverage_increase = min(self.winning_streak - (self.config.winning_streak_threshold - 1), 2)
                self.current_leverage = min(self.config.base_leverage + leverage_increase, self.config.max_leverage)
            else:
                self.current_leverage = self.config.base_leverage
                
        else:  # Losing trade
            self.losing_streak += 1
            self.winning_streak = 0  # Reset winning streak
            
            # Decrease leverage based on losing streak
            if (self.config.enable_dynamic_leverage and 
                self.losing_streak >= self.config.losing_streak_threshold):
                leverage_decrease = min(self.losing_streak - (self.config.losing_streak_threshold - 1), 2)
                self.current_leverage = max(self.config.base_leverage - leverage_decrease, 1)  # Minimum 1:1
            else:
                self.current_leverage = self.config.base_leverage
    
    def _calculate_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[Dict],
        initial_balance: float,
        final_balance: float,
        leverage_risk_factor: float = 1.0
    ) -> PropFirmResult:
        """Calculate metrics for prop firm backtest (same as single_test.py)."""
        
        if not trades:
            return PropFirmResult(
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
                    'lookback_window': self.config.lookback_window,
                    'threshold': self.config.threshold,
                    'position_size_pct': self.config.position_size_pct,
                    'stop_loss_pct': self.config.stop_loss_pct,
                    'take_profit_pct': self.config.take_profit_pct,
                    'max_loss_per_trade': self.config.max_loss_per_trade,
                    'max_daily_loss': self.config.max_daily_loss,
                    'max_overall_loss': self.config.max_overall_loss
                }
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_percentage = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        # Return metrics with leverage effects
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = total_pnl * leverage_risk_factor
        total_return_pct = (total_return / initial_balance) * 100
        
        # Apply leverage risk to final balance
        adjusted_final_balance = final_balance * leverage_risk_factor
        
        # Safety check for extreme values
        if abs(adjusted_final_balance) > initial_balance * self.config.safety_balance_threshold:
            adjusted_final_balance = initial_balance
            total_return = 0.0
            total_return_pct = 0.0
        
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
            returns = equity_df['total_value'].pct_change(fill_method=None).dropna()
            if len(returns) > 0:
                sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            max_drawdown = 0.0
            sharpe_ratio = 0.0
        
        return PropFirmResult(
            initial_balance=initial_balance,
            final_balance=adjusted_final_balance,
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
                'lookback_window': self.config.lookback_window,
                'threshold': self.config.threshold,
                'position_size_pct': self.config.position_size_pct,
                'stop_loss_pct': self.config.stop_loss_pct,
                'take_profit_pct': self.config.take_profit_pct,
                'max_loss_per_trade': self.config.max_loss_per_trade,
                'max_daily_loss': self.config.max_daily_loss,
                'max_overall_loss': self.config.max_overall_loss,
                'base_leverage': self.config.base_leverage,
                'max_leverage': self.config.max_leverage,
                'risk_compounding': self.config.risk_compounding,
                'leverage_risk_factor': leverage_risk_factor,
                'winning_streak': self.winning_streak,
                'losing_streak': self.losing_streak
            }
        )
    
    def _print_detailed_results(self, result: PropFirmResult):
        """Print detailed test results."""
        print("\n" + "=" * 80)
        print("📊 PROP FIRM BOT BACKTEST RESULTS")
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
            elif param == 'base_leverage':
                print(f"   {param.replace('_', ' ').title()}: 1:{value}")
            elif param == 'max_leverage':
                print(f"   {param.replace('_', ' ').title()}: 1:{value}")
            elif param == 'risk_compounding':
                print(f"   {param.replace('_', ' ').title()}: {'Enabled' if value else 'Disabled'}")
            elif param == 'leverage_risk_factor':
                print(f"   {param.replace('_', ' ').title()}: {value:.2f}")
            elif param == 'winning_streak':
                print(f"   {param.replace('_', ' ').title()}: {value}")
            elif param == 'losing_streak':
                print(f"   {param.replace('_', ' ').title()}: {value}")
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
        
        # Leverage Risk Assessment
        leverage_risk_factor = result.parameters_used.get('leverage_risk_factor', 1.0)
        if leverage_risk_factor < 1.0:
            print(f"   ⚠️ LEVERAGE RISK: Margin call effects applied (factor: {leverage_risk_factor:.2f})")
        else:
            print(f"   ✅ No leverage risk effects")


async def main():
    """Main function for prop firm bot."""
    
    print("🚀 Prop Firm Trading Bot")
    print("=" * 60)
    
    # Initialize bot
    bot = PropFirmBot()
    
    # Load existing config if available
    bot.load_config()
    
    # Display current configuration
    bot.display_config()
    
    # Run backtest
    print(f"\n🚀 Starting prop firm backtest...")
    result = await bot.run_backtest(
        timeframe="1y",
        interval="1d",
        initial_balance=100000.0
    )
    
    if result:
        print(f"\n✅ Backtest completed successfully!")
        # Save configuration
        bot.save_config()
    else:
        print(f"\n❌ Backtest failed. Check your configuration.")


if __name__ == "__main__":
    asyncio.run(main()) 