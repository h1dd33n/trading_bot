"""
Test configuration for the trading bot.
"""

import os
from config import get_settings

def setup_test_environment():
    """Set up test environment variables."""
    # Database Configuration (using SQLite for testing)
    os.environ.setdefault('DATABASE__HOST', 'localhost')
    os.environ.setdefault('DATABASE__PORT', '5432')
    os.environ.setdefault('DATABASE__DATABASE', 'trading_bot_test')
    os.environ.setdefault('DATABASE__USERNAME', 'postgres')
    os.environ.setdefault('DATABASE__PASSWORD', 'password')
    os.environ.setdefault('DATABASE__POOL_SIZE', '5')
    os.environ.setdefault('DATABASE__MAX_OVERFLOW', '10')

    # Trading Configuration
    os.environ.setdefault('STRATEGY__STRATEGY_TYPE', 'mean_reversion')
    os.environ.setdefault('STRATEGY__LOOKBACK_WINDOW', '20')
    os.environ.setdefault('STRATEGY__Z_SCORE_THRESHOLD', '2.0')
    os.environ.setdefault('STRATEGY__POSITION_SIZE_PCT', '0.02')
    os.environ.setdefault('STRATEGY__STOP_LOSS_PCT', '0.05')
    os.environ.setdefault('STRATEGY__TAKE_PROFIT_PCT', '0.10')
    os.environ.setdefault('STRATEGY__RSI_PERIOD', '14')
    os.environ.setdefault('STRATEGY__RSI_OVERSOLD', '30')
    os.environ.setdefault('STRATEGY__RSI_OVERBOUGHT', '70')
    os.environ.setdefault('STRATEGY__BOLLINGER_PERIOD', '20')
    os.environ.setdefault('STRATEGY__BOLLINGER_STD', '2.0')

    # Data Configuration
    os.environ.setdefault('DATA__SYMBOLS', '["AAPL", "MSFT", "GOOGL"]')
    os.environ.setdefault('DATA__TIMEFRAMES', '["1h", "4h", "1d"]')
    os.environ.setdefault('DATA__UPDATE_INTERVAL', '60')

    # Risk Management
    os.environ.setdefault('RISK__MAX_PORTFOLIO_RISK', '0.02')
    os.environ.setdefault('RISK__MAX_DRAWDOWN_PCT', '0.20')
    os.environ.setdefault('RISK__KELLY_CRITERION', 'true')
    os.environ.setdefault('RISK__MAX_LEVERAGE', '1.0')
    os.environ.setdefault('RISK__MAX_POSITION_SIZE', '0.10')
    os.environ.setdefault('RISK__MIN_CASH_RESERVE', '0.20')

    # Logging
    os.environ.setdefault('LOGGING__LEVEL', 'INFO')
    os.environ.setdefault('LOGGING__FORMAT', 'json')

    # Debug mode
    os.environ.setdefault('DEBUG', 'true')

if __name__ == "__main__":
    setup_test_environment()
    settings = get_settings()
    print("Test environment configured successfully!")
    print(f"Strategy type: {settings.strategy.strategy_type}")
    print(f"Database: {settings.database.database}") 