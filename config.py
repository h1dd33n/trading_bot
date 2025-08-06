"""
Configuration management for the trading bot.
All parameters are easily tweakable through environment variables or config files.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import os
from enum import Enum


class TradingMode(str, Enum):
    """Trading modes available."""
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class DataSource(str, Enum):
    """Data sources available."""
    YFINANCE = "yfinance"
    ALPACA = "alpaca"
    INTERACTIVE_BROKERS = "ib"


class StrategyType(str, Enum):
    """Strategy types available."""
    MEAN_REVERSION = "mean_reversion"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(default="trading_bot", description="Database name")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(default="Dinyna4ovulahi", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")


class DataConfig(BaseModel):
    """Data configuration."""
    source: DataSource = Field(default=DataSource.YFINANCE, description="Data source")
    symbols: List[str] = Field(default=["EURAUD=X", "EURCAD=X"], description="Trading symbols")
    timeframes: List[str] = Field(default=["1h", "4h", "1d"], description="Timeframes to analyze")
    lookback_days: int = Field(default=252, description="Days of historical data to fetch")
    update_interval: int = Field(default=60, description="Data update interval in seconds")


class StrategyConfig(BaseModel):
    """Strategy configuration with all tweakable parameters."""
    strategy_type: StrategyType = Field(default=StrategyType.MEAN_REVERSION, description="Strategy type")
    
    # Mean reversion parameters
    lookback_window: int = Field(default=30, description="Lookback window for mean calculation")
    threshold: float = Field(default=0.01, description="Threshold for mean reversion signals")
    
    # Signal parameters
    signal_threshold: float = Field(default=0.5, description="Signal strength threshold")
    confirmation_period: int = Field(default=3, description="Confirmation period for signals")
    
    # Position sizing
    position_size_pct: float = Field(default=0.04, description="Position size as percentage of portfolio")
    max_positions: int = Field(default=10, description="Maximum concurrent positions")
    
    # Entry/Exit parameters
    entry_buffer: float = Field(default=0.001, description="Entry buffer percentage")
    exit_buffer: float = Field(default=0.002, description="Exit buffer percentage")
    
    # Risk management
    stop_loss_pct: float = Field(default=0.05, description="Stop loss percentage")
    take_profit_pct: float = Field(default=0.10, description="Take profit percentage")
    max_drawdown_pct: float = Field(default=0.20, description="Maximum drawdown percentage")
    
    # Dynamic risk adjustment
    enable_dynamic_risk: bool = Field(default=True, description="Enable dynamic risk adjustment")
    risk_multiplier: float = Field(default=1.0, description="Risk multiplier based on performance")
    min_risk_multiplier: float = Field(default=0.5, description="Minimum risk multiplier")
    max_risk_multiplier: float = Field(default=2.0, description="Maximum risk multiplier")
    
    # Performance-based adjustments
    performance_lookback: int = Field(default=30, description="Performance lookback period")
    sharpe_threshold: float = Field(default=1.0, description="Sharpe ratio threshold for risk adjustment")
    
    @validator('threshold', 'signal_threshold')
    def validate_thresholds(cls, v):
        """Validate threshold values."""
        if v <= 0:
            raise ValueError("Threshold must be positive")
        return v
    
    @validator('position_size_pct', 'stop_loss_pct', 'take_profit_pct', 'max_drawdown_pct')
    def validate_percentages(cls, v):
        """Validate percentage values."""
        if not 0 < v <= 1:
            raise ValueError("Percentage must be between 0 and 1")
        return v


class RiskConfig(BaseModel):
    """Risk management configuration."""
    max_portfolio_risk: float = Field(default=0.02, description="Maximum portfolio risk per trade")
    correlation_threshold: float = Field(default=0.7, description="Correlation threshold for diversification")
    volatility_lookback: int = Field(default=30, description="Volatility calculation lookback")
    var_confidence: float = Field(default=0.95, description="Value at Risk confidence level")
    max_sector_exposure: float = Field(default=0.3, description="Maximum sector exposure")
    
    # Dynamic position sizing
    kelly_criterion: bool = Field(default=True, description="Use Kelly criterion for position sizing")
    kelly_fraction: float = Field(default=0.25, description="Kelly criterion fraction")
    
    # Portfolio constraints
    min_cash_reserve: float = Field(default=0.1, description="Minimum cash reserve")
    max_leverage: float = Field(default=1.0, description="Maximum leverage")


class ExecutionConfig(BaseModel):
    """Execution configuration."""
    mode: TradingMode = Field(default=TradingMode.PAPER, description="Trading mode")
    broker: str = Field(default="alpaca", description="Broker to use")
    
    # Order parameters
    order_timeout: int = Field(default=30, description="Order timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum order retries")
    retry_delay: int = Field(default=5, description="Retry delay in seconds")
    
    # Slippage and fees
    slippage_pct: float = Field(default=0.001, description="Expected slippage percentage")
    commission_pct: float = Field(default=0.001, description="Commission percentage")
    
    # Broker-specific settings
    alpaca_api_key: Optional[str] = Field(default=None, description="Alpaca API key")
    alpaca_secret_key: Optional[str] = Field(default=None, description="Alpaca secret key")
    alpaca_base_url: str = Field(default="https://paper-api.alpaca.markets", description="Alpaca base URL")
    
    ib_host: str = Field(default="127.0.0.1", description="Interactive Brokers host")
    ib_port: int = Field(default=7497, description="Interactive Brokers port")
    ib_client_id: int = Field(default=1, description="Interactive Brokers client ID")


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    host: str = Field(default="0.0.0.0", description="Dashboard host")
    port: int = Field(default=8501, description="Dashboard port")
    refresh_interval: int = Field(default=30, description="Dashboard refresh interval in seconds")
    enable_notifications: bool = Field(default=True, description="Enable notifications")
    notification_webhook: Optional[str] = Field(default=None, description="Notification webhook URL")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files")


class Settings(BaseSettings):
    """Main settings class that combines all configurations."""
    # Environment
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Performance tracking
    enable_metrics: bool = Field(default=True, description="Enable performance metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Optimization
    enable_optimization: bool = Field(default=False, description="Enable parameter optimization")
    optimization_interval: int = Field(default=7, description="Optimization interval in days")
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def update_strategy_params(params: Dict[str, Any]) -> None:
    """Update strategy parameters dynamically."""
    for key, value in params.items():
        if hasattr(settings.strategy, key):
            setattr(settings.strategy, key, value)
        else:
            raise ValueError(f"Invalid strategy parameter: {key}")


def get_strategy_params() -> Dict[str, Any]:
    """Get current strategy parameters."""
    return settings.strategy.dict()


def validate_config() -> bool:
    """Validate the configuration."""
    try:
        # Validate all configurations
        settings.database
        settings.data
        settings.strategy
        settings.risk
        settings.execution
        settings.dashboard
        settings.logging
        return True
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test configuration
    print("Configuration validation:", validate_config())
    print("Strategy parameters:", get_strategy_params()) 