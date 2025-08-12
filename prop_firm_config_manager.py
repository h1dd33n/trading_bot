#!/usr/bin/env python3
"""
Prop Firm Bot Configuration Manager
Allows easy configuration of all prop firm bot parameters.
"""

import json
from pathlib import Path
from prop_firm_bot import PropFirmBot, PropFirmConfig

class PropFirmConfigManager:
    """Manager for prop firm bot configuration."""
    
    def __init__(self, config_file: str = "prop_firm_config.json"):
        self.config_file = Path(config_file)
        self.bot = PropFirmBot()
        
        # Load existing config if available
        if self.config_file.exists():
            self.bot.load_config(str(self.config_file))
    
    def display_config(self):
        """Display current configuration."""
        self.bot.display_config()
    
    def update_config(self, **kwargs):
        """Update configuration parameters."""
        try:
            self.bot.update_config(**kwargs)
            print("✅ Configuration updated successfully!")
            self.save_config()
        except ValueError as e:
            print(f"❌ Error updating configuration: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        self.bot.save_config(str(self.config_file))
        print(f"✅ Configuration saved to {self.config_file}")
    
    def reset_config(self):
        """Reset configuration to defaults."""
        self.bot = PropFirmBot()
        self.save_config()
        print("✅ Configuration reset to defaults")
    
    def interactive_config(self):
        """Interactive configuration setup."""
        print("\n" + "="*60)
        print("PROP FIRM BOT CONFIGURATION")
        print("="*60)
        
        print("\n📊 Trading Symbols:")
        current_backtest_symbols = ", ".join(self.bot.config.backtest_symbols)
        backtest_symbols_input = input(f"Backtest Symbols (with =X) [{current_backtest_symbols}]: ").strip()
        if backtest_symbols_input:
            backtest_symbols = [s.strip() for s in backtest_symbols_input.split(",")]
            self.bot.update_config(backtest_symbols=backtest_symbols)
        
        current_live_symbols = ", ".join(self.bot.config.live_symbols)
        live_symbols_input = input(f"Live Symbols (with .pro) [{current_live_symbols}]: ").strip()
        if live_symbols_input:
            live_symbols = [s.strip() for s in live_symbols_input.split(",")]
            self.bot.update_config(live_symbols=live_symbols)
        
        print("\n📈 Strategy Parameters (same as single_test.py):")
        lookback = input(f"Lookback Window [{self.bot.config.lookback_window}]: ").strip()
        if lookback:
            self.bot.update_config(lookback_window=int(lookback))
        
        threshold = input(f"Threshold (0.01 = 1%) [{self.bot.config.threshold}]: ").strip()
        if threshold:
            self.bot.update_config(threshold=float(threshold))
        
        position_size = input(f"Position Size (0.02 = 2%) [{self.bot.config.position_size_pct}]: ").strip()
        if position_size:
            self.bot.update_config(position_size_pct=float(position_size))
        
        stop_loss = input(f"Stop Loss (0.05 = 5%) [{self.bot.config.stop_loss_pct}]: ").strip()
        if stop_loss:
            self.bot.update_config(stop_loss_pct=float(stop_loss))
        
        take_profit = input(f"Take Profit (0.10 = 10%) [{self.bot.config.take_profit_pct}]: ").strip()
        if take_profit:
            self.bot.update_config(take_profit_pct=float(take_profit))
        
        print("\n🛡️ Risk Management (Configurable for Prop Firm):")
        max_loss_per_trade = input(f"Max Loss Per Trade (0.01 = 1%) [{self.bot.config.max_loss_per_trade}]: ").strip()
        if max_loss_per_trade:
            self.bot.update_config(max_loss_per_trade=float(max_loss_per_trade))
        
        max_daily_loss = input(f"Max Daily Loss (0.02 = 2%) [{self.bot.config.max_daily_loss}]: ").strip()
        if max_daily_loss:
            self.bot.update_config(max_daily_loss=float(max_daily_loss))
        
        max_overall_loss = input(f"Max Overall Loss (0.04 = 4%) [{self.bot.config.max_overall_loss}]: ").strip()
        if max_overall_loss:
            self.bot.update_config(max_overall_loss=float(max_overall_loss))
        
        max_positions = input(f"Max Positions [{self.bot.config.max_positions}]: ").strip()
        if max_positions:
            self.bot.update_config(max_positions=int(max_positions))
        
        print("\n⚙️ Leverage Settings (same as single_test.py):")
        base_leverage = input(f"Base Leverage (1.0 = 1:1) [{self.bot.config.base_leverage}]: ").strip()
        if base_leverage:
            self.bot.update_config(base_leverage=float(base_leverage))
        
        max_leverage = input(f"Max Leverage (5.0 = 1:5) [{self.bot.config.max_leverage}]: ").strip()
        if max_leverage:
            self.bot.update_config(max_leverage=float(max_leverage))
        
        risk_compounding = input(f"Risk Compounding (y/n) [{'y' if self.bot.config.risk_compounding else 'n'}]: ").strip().lower()
        if risk_compounding in ['y', 'yes']:
            self.bot.update_config(risk_compounding=True)
        elif risk_compounding in ['n', 'no']:
            self.bot.update_config(risk_compounding=False)
        
        dynamic_leverage = input(f"Dynamic Leverage (y/n) [{'y' if self.bot.config.enable_dynamic_leverage else 'n'}]: ").strip().lower()
        if dynamic_leverage in ['y', 'yes']:
            self.bot.update_config(enable_dynamic_leverage=True)
        elif dynamic_leverage in ['n', 'no']:
            self.bot.update_config(enable_dynamic_leverage=False)
        
        winning_streak = input(f"Winning Streak Threshold [{self.bot.config.winning_streak_threshold}]: ").strip()
        if winning_streak:
            self.bot.update_config(winning_streak_threshold=int(winning_streak))
        
        losing_streak = input(f"Losing Streak Threshold [{self.bot.config.losing_streak_threshold}]: ").strip()
        if losing_streak:
            self.bot.update_config(losing_streak_threshold=int(losing_streak))
        
        # Save configuration
        self.save_config()
        
        print("\n✅ Configuration updated and saved!")
        print("\nCurrent Configuration:")
        self.display_config()


def main():
    """Main function for configuration manager."""
    import asyncio
    
    print("⚙️ Prop Firm Bot Configuration Manager")
    print("=" * 60)
    
    manager = PropFirmConfigManager()
    
    while True:
        print("\nOptions:")
        print("1. Display Current Configuration")
        print("2. Interactive Configuration")
        print("3. Update Specific Parameter")
        print("4. Reset to Defaults")
        print("5. Run Backtest")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            manager.display_config()
        
        elif choice == "2":
            manager.interactive_config()
        
        elif choice == "3":
            print("\nAvailable parameters:")
            print("- backtest_symbols: List of backtest symbols (with =X)")
            print("- live_symbols: List of live trading symbols (with .pro)")
            print("- lookback_window: Lookback window for SMA")
            print("- threshold: Signal threshold (0.01 = 1%)")
            print("- position_size_pct: Position size (0.02 = 2%)")
            print("- stop_loss_pct: Stop loss (0.05 = 5%)")
            print("- take_profit_pct: Take profit (0.10 = 10%)")
            print("- max_loss_per_trade: Max loss per trade (0.01 = 1%)")
            print("- max_daily_loss: Max daily loss (0.02 = 2%)")
            print("- max_overall_loss: Max overall loss (0.04 = 4%)")
            print("- max_positions: Maximum concurrent positions")
            print("- base_leverage: Base leverage (1.0 = 1:1)")
            print("- max_leverage: Maximum leverage (5.0 = 1:5)")
            print("- risk_compounding: Enable risk compounding (True/False)")
            print("- enable_dynamic_leverage: Enable dynamic leverage (True/False)")
            print("- winning_streak_threshold: Winning streak threshold")
            print("- losing_streak_threshold: Losing streak threshold")
            
            param = input("Enter parameter name: ").strip()
            value_input = input("Enter new value: ").strip()
            
            try:
                # Convert value to appropriate type
                if param in ['backtest_symbols', 'live_symbols']:
                    value = [s.strip() for s in value_input.split(",")]
                elif param in ['lookback_window', 'max_positions', 'winning_streak_threshold', 'losing_streak_threshold']:
                    value = int(value_input)
                elif param in ['risk_compounding', 'enable_dynamic_leverage']:
                    value = value_input.lower() in ['true', 'yes', 'y', '1']
                else:
                    value = float(value_input)
                
                manager.update_config(**{param: value})
                print(f"✅ Updated {param} to {value}")
                
            except (ValueError, TypeError) as e:
                print(f"❌ Error: {e}")
        
        elif choice == "4":
            confirm = input("Are you sure you want to reset to defaults? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                manager.reset_config()
        
        elif choice == "5":
            print("\nRunning backtest...")
            asyncio.run(manager.bot.run_backtest())
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main() 