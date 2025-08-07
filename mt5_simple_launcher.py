#!/usr/bin/env python3
"""
Simple MT5 Bots Launcher - No config dependency
Run both regular and prop firm MT5 trading bots with monitoring.

TRADING STRATEGY EXPLANATION:
============================

REGULAR MT5 BOT TRADING CRITERIA:
- Uses RSI (14-period) + SMA20 combination
- BUY Signal: RSI < 30 AND price below SMA20
- SELL Signal: RSI > 70 AND price above SMA20
- Position sizing: Based on pip value and risk management
- Stop Loss: 20 pips from entry
- Take Profit: 40 pips from entry

PROP FIRM MT5 BOT TRADING CRITERIA (More Conservative):
- Uses RSI (14-period) + SMA20 + ATR combination
- BUY Signal: RSI < 25 AND price 0.5% below SMA20
- SELL Signal: RSI > 75 AND price 0.5% above SMA20
- Position sizing: 1% of capital per trade (ATR-based)
- Stop Loss: 1.5 ATR from entry
- Take Profit: 3 ATR from entry
- Risk Limits: 2% daily loss limit, 4% overall loss limit
- Max Positions: 3 concurrent positions

WHEN BOTS TAKE TRADES:
======================
1. Technical Conditions Met:
   - RSI reaches oversold/overbought levels
   - Price confirms trend with SMA20
   - ATR provides volatility context (prop firm only)

2. Risk Management Checks:
   - Within daily/overall loss limits
   - Not at maximum position count
   - No existing position in same symbol
   - Sufficient account balance

3. Market Conditions:
   - Valid market data available
   - Indicators not showing NaN values
   - Sufficient liquidity for execution

4. Execution Requirements:
   - MT5 connection active
   - Market hours (if applicable)
   - Order execution possible
"""

import asyncio
import logging
import argparse
from typing import Dict, Any
from datetime import datetime
import signal
import sys
import os

# Add mt5 directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mt5'))

# Import MT5 modules
from mt5.mt5_trading_bot import MT5TradingBot
from mt5.mt5_prop_firm_bot import MT5PropFirmBot, YFinanceBacktester
from mt5.mt5_config import AccountType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_bots.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MT5BotsLauncher:
    """Launcher for MT5 trading bots."""
    
    def __init__(self):
        self.regular_bot = None
        self.prop_firm_bot = None
        self.running = False
        
    async def initialize_bots(self, run_regular: bool = True, run_prop_firm: bool = True) -> bool:
        """Initialize the trading bots."""
        try:
            if run_regular:
                logger.info("Initializing regular MT5 bot...")
                logger.info("Regular Bot Strategy: RSI < 30 (BUY) or RSI > 70 (SELL) + SMA20 confirmation")
                self.regular_bot = MT5TradingBot(AccountType.REGULAR)
                if not await self.regular_bot.initialize():
                    logger.error("Failed to initialize regular bot")
                    return False
                logger.info("Regular MT5 bot initialized successfully")
            
            if run_prop_firm:
                logger.info("Initializing prop firm MT5 bot...")
                logger.info("Prop Firm Strategy: RSI < 25 (BUY) or RSI > 75 (SELL) + SMA20 + 0.5% buffer")
                self.prop_firm_bot = MT5PropFirmBot()
                if not await self.prop_firm_bot.initialize():
                    logger.error("Failed to initialize prop firm bot")
                    return False
                logger.info("Prop firm MT5 bot initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing bots: {e}")
            return False
    
    async def start_bots(self, run_regular: bool = True, run_prop_firm: bool = True):
        """Start the trading bots."""
        try:
            if run_regular and self.regular_bot:
                logger.info("Starting regular MT5 bot...")
                logger.info("Waiting for: RSI < 30 (BUY) or RSI > 70 (SELL) with SMA20 confirmation")
                await self.regular_bot.start_trading()
            
            if run_prop_firm and self.prop_firm_bot:
                logger.info("Starting prop firm MT5 bot...")
                logger.info("Waiting for: RSI < 25 (BUY) or RSI > 75 (SELL) with SMA20 + 0.5% buffer")
                await self.prop_firm_bot.start_trading()
            
            self.running = True
            logger.info("All bots started successfully")
            
        except Exception as e:
            logger.error(f"Error starting bots: {e}")
    
    async def stop_bots(self):
        """Stop the trading bots."""
        try:
            if self.regular_bot:
                logger.info("Stopping regular MT5 bot...")
                await self.regular_bot.stop_trading()
            
            if self.prop_firm_bot:
                logger.info("Stopping prop firm MT5 bot...")
                await self.prop_firm_bot.stop_trading()
            
            self.running = False
            logger.info("All bots stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bots: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            await self.stop_bots()
            
            # Cleanup MT5 connection
            from mt5.mt5_config import get_mt5_connection
            connection = get_mt5_connection(AccountType.REGULAR)
            connection.shutdown()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of all bots."""
        status = {
            "running": self.running,
            "regular_bot": {
                "initialized": self.regular_bot is not None,
                "active": self.regular_bot.is_running if self.regular_bot else False
            },
            "prop_firm_bot": {
                "initialized": self.prop_firm_bot is not None,
                "active": self.prop_firm_bot.is_running if self.prop_firm_bot else False
            }
        }
        return status
    
    async def run_backtest(self, symbols: list = None, start_date: str = "2024-01-01", end_date: str = "2024-12-31"):
        """Run YFinance backtest for prop firm bot."""
        try:
            logger.info("=" * 80)
            logger.info("STARTING YFINANCE BACKTEST")
            logger.info("=" * 80)
            
            if symbols is None:
                symbols = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURAUD=X", "EURCAD=X"]
            
            logger.info(f"Symbols: {', '.join(symbols)}")
            logger.info(f"Period: {start_date} to {end_date}")
            logger.info(f"Initial Capital: $100,000")
            logger.info("")
            
            backtester = YFinanceBacktester(
                symbols=symbols,
                initial_capital=100000
            )
            
            result = backtester.run_backtest(start_date, end_date)
            
            # Display results in a readable format
            self._display_backtest_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return None
    
    def _display_backtest_results(self, result: Dict[str, Any]):
        """Display backtest results in a readable format."""
        try:
            logger.info("=" * 80)
            logger.info("BACKTEST RESULTS")
            logger.info("=" * 80)
            
            # Display individual symbol results
            logger.info("INDIVIDUAL SYMBOL PERFORMANCE:")
            logger.info("-" * 60)
            
            for symbol, symbol_result in result.get("symbol_results", {}).items():
                if "error" in symbol_result:
                    logger.warning(f"ERROR {symbol}: {symbol_result['error']}")
                    continue
                
                total_trades = symbol_result.get("total_trades", 0)
                winning_trades = symbol_result.get("winning_trades", 0)
                losing_trades = symbol_result.get("losing_trades", 0)
                win_rate = symbol_result.get("win_rate", 0) * 100
                total_pnl = symbol_result.get("total_pnl", 0)
                return_pct = symbol_result.get("return_pct", 0)
                
                # Determine performance indicator
                if return_pct > 0:
                    indicator = "[PROFIT]"
                elif return_pct < 0:
                    indicator = "[LOSS]"
                else:
                    indicator = "[NEUTRAL]"
                
                logger.info(f"{indicator} {symbol}:")
                logger.info(f"   Trades: {total_trades} (W: {winning_trades}, L: {losing_trades})")
                logger.info(f"   Win Rate: {win_rate:.1f}%")
                logger.info(f"   P&L: ${total_pnl:,.2f}")
                logger.info(f"   Return: {return_pct:.2f}%")
                logger.info("")
            
            # Display overall results
            total_result = result.get("total_result", {})
            if "error" not in total_result:
                logger.info("OVERALL PERFORMANCE:")
                logger.info("-" * 60)
                
                total_trades = total_result.get("total_trades", 0)
                total_pnl = total_result.get("total_pnl", 0)
                winning_trades = total_result.get("winning_trades", 0)
                losing_trades = total_result.get("losing_trades", 0)
                overall_win_rate = total_result.get("overall_win_rate", 0) * 100
                overall_return = total_result.get("overall_return_pct", 0)
                avg_win = total_result.get("avg_win", 0)
                avg_loss = total_result.get("avg_loss", 0)
                profit_factor = total_result.get("profit_factor", 0)
                
                # Determine overall performance indicator
                if overall_return > 0:
                    overall_indicator = "[PROFITABLE]"
                elif overall_return < 0:
                    overall_indicator = "[LOSS]"
                else:
                    overall_indicator = "[NEUTRAL]"
                
                logger.info(f"{overall_indicator} Total Trades: {total_trades}")
                logger.info(f"   Winning: {winning_trades}, Losing: {losing_trades}")
                logger.info(f"   Win Rate: {overall_win_rate:.1f}%")
                logger.info(f"   Total P&L: ${total_pnl:,.2f}")
                logger.info(f"   Overall Return: {overall_return:.2f}%")
                logger.info(f"   Avg Win: ${avg_win:,.2f}")
                logger.info(f"   Avg Loss: ${avg_loss:,.2f}")
                logger.info(f"   Profit Factor: {profit_factor:.2f}")
                logger.info("")
                
                # Risk management summary
                logger.info("RISK MANAGEMENT SUMMARY:")
                logger.info("-" * 60)
                logger.info("  - 2% Daily Loss Limit Enforced")
                logger.info("  - 4% Overall Loss Limit Enforced")
                logger.info("  - ATR-based Position Sizing")
                logger.info("  - Maximum 3 Concurrent Positions")
                logger.info("  - 1.5 ATR Stop Loss")
                logger.info("  - 3 ATR Take Profit")
                logger.info("")
                
                # Performance rating
                if overall_return > 20:
                    rating = "EXCELLENT"
                elif overall_return > 10:
                    rating = "GOOD"
                elif overall_return > 0:
                    rating = "PROFITABLE"
                elif overall_return > -10:
                    rating = "SLIGHT LOSS"
                else:
                    rating = "POOR"
                
                logger.info(f"PERFORMANCE RATING: {rating}")
                
            else:
                logger.error(f"Error in total results: {total_result['error']}")
            
            logger.info("=" * 80)
            logger.info("BACKTEST COMPLETED")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}")
    
    async def monitor_bots(self):
        """Monitor bot status periodically with detailed trading criteria explanations."""
        while self.running:
            try:
                status = self.get_status()
                
                # Get detailed prop firm status
                if self.prop_firm_bot and hasattr(self.prop_firm_bot, 'get_detailed_status'):
                    detailed_status = self.prop_firm_bot.get_detailed_status()
                    
                    logger.info("=" * 80)
                    logger.info("PROP FIRM BOT STATUS & TRADING CRITERIA")
                    logger.info("=" * 80)
                    
                    if "account_info" in detailed_status and detailed_status["account_info"]:
                        account = detailed_status["account_info"]
                        logger.info(f"Account: {account.get('login', 'N/A')}")
                        logger.info(f"Balance: ${account.get('balance', 0):,.2f}")
                        logger.info(f"Equity: ${account.get('equity', 0):,.2f}")
                        logger.info(f"Profit: ${account.get('profit', 0):,.2f}")
                    
                    logger.info(f"Positions: {len(detailed_status.get('positions', []))}")
                    logger.info(f"Waiting for trades: {detailed_status.get('waiting_for_trades', False)}")
                    logger.info(f"Can take trades: {detailed_status.get('can_take_trades', False)}")
                    
                    # Show market conditions with trading criteria explanations
                    market_conditions = detailed_status.get('market_conditions', {})
                    logger.info("")
                    logger.info("MARKET CONDITIONS & TRADING SIGNALS:")
                    logger.info("-" * 60)
                    
                    for symbol, conditions in market_conditions.items():
                        if "error" not in conditions:
                            current_price = conditions.get('current_price', 0)
                            sma_20 = conditions.get('sma_20', 0)
                            rsi = conditions.get('rsi', 0)
                            atr = conditions.get('atr', 0)
                            price_vs_sma = conditions.get('price_vs_sma', 0)
                            signal_ready = conditions.get('signal_ready', False)
                            
                            logger.info(f"  {symbol}:")
                            logger.info(f"    Price: {current_price:.5f}")
                            logger.info(f"    SMA20: {sma_20:.5f}")
                            logger.info(f"    RSI: {rsi:.2f}")
                            logger.info(f"    ATR: {atr:.5f}")
                            logger.info(f"    Price vs SMA: {price_vs_sma:.2f}%")
                            logger.info(f"    Signal Ready: {signal_ready}")
                            
                            # Explain why signal is ready or not
                            if signal_ready:
                                if rsi < 25:
                                    logger.info(f"    [BUY] BUY SIGNAL: RSI={rsi:.2f} < 25 (oversold)")
                                    if current_price < sma_20 * 0.995:
                                        logger.info(f"    [OK] Price {current_price:.5f} is 0.5% below SMA20 {sma_20:.5f}")
                                    else:
                                        logger.info(f"    [WAIT] Price not 0.5% below SMA20 - waiting for confirmation")
                                elif rsi > 75:
                                    logger.info(f"    [SELL] SELL SIGNAL: RSI={rsi:.2f} > 75 (overbought)")
                                    if current_price > sma_20 * 1.005:
                                        logger.info(f"    [OK] Price {current_price:.5f} is 0.5% above SMA20 {sma_20:.5f}")
                                    else:
                                        logger.info(f"    [WAIT] Price not 0.5% above SMA20 - waiting for confirmation")
                            else:
                                if rsi >= 25 and rsi <= 75:
                                    logger.info(f"    [NEUTRAL] NO SIGNAL: RSI={rsi:.2f} is between 25-75 (neutral)")
                                elif rsi < 25:
                                    logger.info(f"    [WAITING] RSI={rsi:.2f} < 25 but price not 0.5% below SMA20")
                                elif rsi > 75:
                                    logger.info(f"    [WAITING] RSI={rsi:.2f} > 75 but price not 0.5% above SMA20")
                            
                            logger.info("")
                        else:
                            logger.warning(f"  {symbol}: {conditions['error']}")
                    
                    # Show risk management status
                    logger.info("RISK MANAGEMENT STATUS:")
                    logger.info("-" * 60)
                    logger.info("  Trading Criteria:")
                    logger.info("    • RSI < 25 (BUY) or RSI > 75 (SELL)")
                    logger.info("    • Price 0.5% below/above SMA20")
                    logger.info("    • ATR-based position sizing")
                    logger.info("    • 1.5 ATR stop loss, 3 ATR take profit")
                    logger.info("    • Max 3 concurrent positions")
                    logger.info("    • 2% daily loss limit, 4% overall loss limit")
                    logger.info("")
                    
                # Show regular bot status if available
                if self.regular_bot and hasattr(self.regular_bot, 'get_status'):
                    regular_status = self.regular_bot.get_status()
                    logger.info("REGULAR BOT STATUS:")
                    logger.info("-" * 60)
                    logger.info("  Trading Criteria:")
                    logger.info("    • RSI < 30 (BUY) or RSI > 70 (SELL)")
                    logger.info("    • Price below/above SMA20")
                    logger.info("    • 20 pip stop loss, 40 pip take profit")
                    logger.info("")
                
                logger.info("=" * 80)
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                await asyncio.sleep(60)


async def main():
    """Main function to run the MT5 bots."""
    parser = argparse.ArgumentParser(description="MT5 Trading Bots Launcher")
    parser.add_argument("--regular", action="store_true", help="Run regular MT5 bot")
    parser.add_argument("--prop-firm", action="store_true", help="Run prop firm MT5 bot")
    parser.add_argument("--backtest", action="store_true", help="Run YFinance backtest only")
    parser.add_argument("--monitor", action="store_true", help="Enable bot monitoring")
    parser.add_argument("--duration", type=int, default=0, help="Run duration in seconds (0 = run indefinitely)")
    
    args = parser.parse_args()
    
    # If no specific bot is selected, run both
    if not args.regular and not args.prop_firm and not args.backtest:
        args.regular = True
        args.prop_firm = True
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping bots...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher = MT5BotsLauncher()
    
    try:
        if args.backtest:
            # Run backtest only
            await launcher.run_backtest()
            return
        
        # Initialize and start bots
        if await launcher.initialize_bots(args.regular, args.prop_firm):
            await launcher.start_bots(args.regular, args.prop_firm)
            
            # Start monitoring if requested
            if args.monitor:
                monitor_task = asyncio.create_task(launcher.monitor_bots())
            
            # Run for specified duration or indefinitely
            if args.duration > 0:
                logger.info(f"Running bots for {args.duration} seconds...")
                await asyncio.sleep(args.duration)
            else:
                logger.info("Running bots indefinitely. Press Ctrl+C to stop.")
                while True:
                    await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await launcher.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 