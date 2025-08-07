#!/usr/bin/env python3
"""
Simple backtest test script.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mt5'))

from mt5.mt5_prop_firm_bot import YFinanceBacktester

def main():
    """Run a simple backtest."""
    print("Starting YFinance backtest...")
    
    # Create backtester
    backtester = YFinanceBacktester(
        symbols=["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURAUD=X", "EURCAD=X"],
        initial_capital=100000
    )
    
    # Run backtest
    result = backtester.run_backtest("2024-01-01", "2024-12-31")
    
    print("Backtest completed!")
    print(f"Results: {result}")

if __name__ == "__main__":
    main() 