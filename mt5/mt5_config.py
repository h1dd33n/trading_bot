"""
MT5 Configuration and connection management.
Handles different account types and connection settings.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)


class AccountType(str, Enum):
    """MT5 account types."""
    REGULAR = "regular"
    PROP_FIRM = "prop_firm"


class MT5AccountConfig(BaseModel):
    """MT5 account configuration."""
    account_type: AccountType
    server: str
    login: int
    password: str
    symbols: list[str]
    
    # Risk management settings
    max_daily_loss_pct: float = Field(default=0.02, description="Maximum daily loss percentage")
    max_overall_loss_pct: float = Field(default=0.04, description="Maximum overall loss percentage")
    
    # Position sizing
    position_size_pct: float = Field(default=0.02, description="Position size as percentage of account")
    max_positions: int = Field(default=5, description="Maximum concurrent positions")
    
    # Stop loss and take profit
    stop_loss_pct: float = Field(default=0.02, description="Stop loss percentage")
    take_profit_pct: float = Field(default=0.04, description="Take profit percentage")


class MT5Connection:
    """MT5 connection manager."""
    
    def __init__(self, config: MT5AccountConfig):
        self.config = config
        self.connected = False
        self.account_info = None
    
    def connect(self) -> bool:
        """Connect to MT5 terminal."""
        try:
            # Initialize MT5
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login to account
            if not mt5.login(
                login=self.config.login,
                password=self.config.password,
                server=self.config.server
            ):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                return False
            
            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.error("Failed to get account info")
                return False
            
            self.connected = True
            logger.info(f"Connected to MT5 account: {self.account_info.login}")
            logger.info(f"Account balance: {self.account_info.balance}")
            logger.info(f"Account equity: {self.account_info.equity}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5."""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                logger.info("Disconnected from MT5")
        except Exception as e:
            logger.error(f"Error disconnecting from MT5: {e}")
    
    def shutdown(self):
        """Shutdown MT5 connection (alias for disconnect)."""
        self.disconnect()
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information."""
        if not self.connected or self.account_info is None:
            return None
        
        return {
            "login": self.account_info.login,
            "balance": self.account_info.balance,
            "equity": self.account_info.equity,
            "margin": self.account_info.margin,
            "free_margin": self.account_info.margin_free,
            "profit": self.account_info.profit,
            "currency": self.account_info.currency
        }
    
    def get_positions(self) -> list:
        """Get current open positions."""
        if not self.connected:
            return []
        
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        return [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "buy" if pos.type == mt5.POSITION_TYPE_BUY else "sell",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "profit": pos.profit,
                "swap": pos.swap,
                "time": pos.time
            }
            for pos in positions
        ]
    
    def get_daily_pnl(self) -> float:
        """Get daily P&L."""
        if not self.connected or self.account_info is None:
            return 0.0
        
        # This is a simplified calculation
        # In a real implementation, you'd track daily P&L more accurately
        return self.account_info.profit
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """Check if account is within risk limits."""
        if not self.connected or self.account_info is None:
            return {"within_limits": False, "daily_limit_exceeded": True, "overall_limit_exceeded": True}
        
        daily_pnl = self.get_daily_pnl()
        balance = self.account_info.balance
        
        daily_loss_pct = abs(min(daily_pnl, 0)) / balance if balance > 0 else 0
        overall_loss_pct = (balance - self.account_info.equity) / balance if balance > 0 else 0
        
        daily_limit_exceeded = daily_loss_pct > self.config.max_daily_loss_pct
        overall_limit_exceeded = overall_loss_pct > self.config.max_overall_loss_pct
        
        return {
            "within_limits": not (daily_limit_exceeded or overall_limit_exceeded),
            "daily_limit_exceeded": daily_limit_exceeded,
            "overall_limit_exceeded": overall_limit_exceeded,
            "daily_loss_pct": daily_loss_pct,
            "overall_loss_pct": overall_loss_pct
        }


# Account configurations
REGULAR_ACCOUNT_CONFIG = MT5AccountConfig(
    account_type=AccountType.REGULAR,
    server="ACGMarkets-Main",
    login=2194718,
    password="vUD&V86dwc",
    symbols=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
    max_daily_loss_pct=0.05,  # 5% for regular account
    max_overall_loss_pct=0.10,  # 10% for regular account
    position_size_pct=0.02,
    max_positions=10,
    stop_loss_pct=0.02,
    take_profit_pct=0.04
)

PROP_FIRM_ACCOUNT_CONFIG = MT5AccountConfig(
    account_type=AccountType.PROP_FIRM,
    server="ACGMarkets-Main",
    login=2194718,
    password="vUD&V86dwc",
    symbols=["AUDUSD.pro", "EURAUD.pro"],  # AUDUSD.pro and EURAUD.pro as requested
    max_daily_loss_pct=0.02,  # 2% for prop firm
    max_overall_loss_pct=0.04,  # 4% for prop firm
    position_size_pct=0.01,  # Smaller position size for prop firm
    max_positions=3,  # Fewer positions for prop firm
    stop_loss_pct=0.015,  # Tighter stop loss
    take_profit_pct=0.03
)


def get_mt5_connection(account_type: AccountType) -> MT5Connection:
    """Get MT5 connection for specified account type."""
    if account_type == AccountType.REGULAR:
        config = REGULAR_ACCOUNT_CONFIG
    elif account_type == AccountType.PROP_FIRM:
        config = PROP_FIRM_ACCOUNT_CONFIG
    else:
        raise ValueError(f"Unknown account type: {account_type}")
    
    return MT5Connection(config) 