#!/usr/bin/env python3
"""
MT5 Bots Launcher - Root Level Script
Run both regular and prop firm MT5 trading bots with monitoring.
"""

import asyncio
import logging
import argparse
from typing import Dict, Any
from datetime import datetime
import signal
import sys

# Import MT5 modules from the mt5 package
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
                self.regular_bot = MT5TradingBot(AccountType.REGULAR)
                if not await self.regular_bot.initialize():
                    logger.error("Failed to initialize regular bot")
                    return False
                logger.info("Regular MT5 bot initialized successfully")
            
            if run_prop_firm:
                logger.info("Initializing prop firm MT5 bot...")
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
                await self.regular_bot.start_trading()
            
            if run_prop_firm and self.prop_firm_bot:
                logger.info("Starting prop firm MT5 bot...")
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
            logger.info("Starting YFinance backtest...")
            
            if symbols is None:
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
            
            backtester = YFinanceBacktester()
            results = await backtester.run_backtest(symbols, start_date, end_date)
            
            logger.info("Backtest completed successfully")
            logger.info(f"Results: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return None
    
    async def monitor_bots(self, interval: int = 60):
        """Monitor bots status periodically."""
        logger.info(f"Starting bot monitoring (interval: {interval}s)")
        
        while self.running:
            try:
                status = self.get_status()
                logger.info(f"Bot Status: {status}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                await asyncio.sleep(interval)


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