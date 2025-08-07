"""
MT5 Trading Bots Module
Contains MT5 trading bots for regular and prop firm accounts.
"""

from .mt5_config import (
    AccountType,
    MT5AccountConfig,
    MT5Connection,
    get_mt5_connection,
    REGULAR_ACCOUNT_CONFIG,
    PROP_FIRM_ACCOUNT_CONFIG
)

from .mt5_trading_bot import MT5TradingBot
from .mt5_prop_firm_bot import MT5PropFirmBot, YFinanceBacktester, PropFirmLimits
from .run_mt5_bots import MT5BotsLauncher

__all__ = [
    "AccountType",
    "MT5AccountConfig", 
    "MT5Connection",
    "get_mt5_connection",
    "REGULAR_ACCOUNT_CONFIG",
    "PROP_FIRM_ACCOUNT_CONFIG",
    "MT5TradingBot",
    "MT5PropFirmBot",
    "YFinanceBacktester",
    "PropFirmLimits",
    "MT5BotsLauncher"
]

__version__ = "1.0.0" 