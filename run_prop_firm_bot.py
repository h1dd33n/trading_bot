#!/usr/bin/env python3
"""
Prop Firm Bot Launcher
Simple launcher for the prop firm trading bot.
Supports both backtesting and live trading.
"""

import asyncio
import argparse
from prop_firm_bot import PropFirmBot
from prop_firm_config_manager import PropFirmConfigManager

async def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(description="Prop Firm Trading Bot Launcher")
    parser.add_argument("--config", action="store_true", help="Open configuration manager")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    parser.add_argument("--backtest", action="store_true", help="Run backtest")
    parser.add_argument("--live", action="store_true", help="Run live trading")
    parser.add_argument("--timeframe", default="1y", help="Backtest timeframe (default: 1y)")
    parser.add_argument("--interval", default="1d", help="Backtest interval (default: 1d)")
    parser.add_argument("--balance", type=float, default=100000.0, help="Initial balance (default: 100000)")
    parser.add_argument("--update", nargs=2, metavar=("PARAM", "VALUE"), help="Update specific parameter")
    parser.add_argument("--test-connection", action="store_true", help="Test MT5 connection")
    
    args = parser.parse_args()
    
    print("🚀 Prop Firm Trading Bot Launcher")
    print("=" * 60)
    
    if args.config:
        # Open configuration manager
        manager = PropFirmConfigManager()
        manager.interactive_config()
    
    elif args.show_config:
        # Show current configuration
        manager = PropFirmConfigManager()
        manager.display_config()
    
    elif args.test_connection:
        # Test MT5 connection
        bot = PropFirmBot()
        bot.load_config()
        
        print("🔌 Testing MT5 connection...")
        if bot.connect_mt5():
            print("✅ MT5 connection successful!")
            
            # Get account info
            import MetaTrader5 as mt5
            account_info = mt5.account_info()
            print(f"📊 Account: {account_info.login}")
            print(f"💰 Balance: ${account_info.balance:,.2f}")
            print(f"📈 Equity: ${account_info.equity:,.2f}")
            print(f"🏦 Server: {account_info.server}")
            
            # Get available symbols
            symbols = bot.get_available_symbols()
            print(f"📊 Available symbols: {len(symbols)}")
            
            # Check our symbols
            for symbol in bot.config.live_symbols:
                if symbol in symbols:
                    print(f"✅ {symbol} is available")
                else:
                    print(f"❌ {symbol} is NOT available")
            
            bot.disconnect_mt5()
        else:
            print("❌ MT5 connection failed!")
    
    elif args.update:
        # Update specific parameter
        param, value = args.update
        manager = PropFirmConfigManager()
        
        try:
            # Convert value to appropriate type
            if param in ['backtest_symbols', 'live_symbols']:
                value = [s.strip() for s in value.split(",")]
            elif param in ['lookback_window', 'max_positions', 'winning_streak_threshold', 'losing_streak_threshold']:
                value = int(value)
            elif param in ['risk_compounding', 'enable_dynamic_leverage', 'enable_live_trading', 'demo_account']:
                value = value.lower() in ['true', 'yes', 'y', '1']
            else:
                value = float(value)
            
            manager.update_config(**{param: value})
            print(f"✅ Updated {param} to {value}")
            
        except (ValueError, TypeError) as e:
            print(f"❌ Error: {e}")
    
    elif args.backtest:
        # Run backtest
        bot = PropFirmBot()
        bot.load_config()
        
        print(f"Running backtest with:")
        print(f"  Timeframe: {args.timeframe}")
        print(f"  Interval: {args.interval}")
        print(f"  Initial Balance: ${args.balance:,.2f}")
        print()
        
        result = await bot.run_backtest(
            timeframe=args.timeframe,
            interval=args.interval,
            initial_balance=args.balance
        )
        
        if result:
            print(f"\n✅ Backtest completed successfully!")
        else:
            print(f"\n❌ Backtest failed.")
    
    elif args.live:
        # Run live trading
        bot = PropFirmBot()
        bot.load_config()
        
        print("⚠️ WARNING: Starting LIVE TRADING!")
        print("This will place real orders on your MT5 account.")
        print("Make sure you understand the risks involved.")
        
        confirm = input("\nDo you want to continue? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("Live trading cancelled.")
            return
        
        print(f"\n🚀 Starting live trading...")
        print(f"📊 Live Symbols: {', '.join(bot.config.live_symbols)}")
        print(f"📈 Backtest Symbols: {', '.join(bot.config.backtest_symbols)}")
        
        try:
            await bot.run_live_trading()
        except KeyboardInterrupt:
            print("\n🛑 Live trading stopped by user")
        except Exception as e:
            print(f"\n❌ Live trading error: {e}")
    
    else:
        # Default: show help
        parser.print_help()
        print("\nExamples:")
        print("  python run_prop_firm_bot.py --config")
        print("  python run_prop_firm_bot.py --show-config")
        print("  python run_prop_firm_bot.py --backtest")
        print("  python run_prop_firm_bot.py --backtest --timeframe 2y --balance 50000")
        print("  python run_prop_firm_bot.py --live")
        print("  python run_prop_firm_bot.py --test-connection")
        print("  python run_prop_firm_bot.py --update max_daily_loss 0.03")
        print("  python run_prop_firm_bot.py --update live_symbols 'EURAUD.pro,EURCAD.pro'")


if __name__ == "__main__":
    asyncio.run(main()) 