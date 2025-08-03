"""
Basic tests for the trading bot components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from config import get_settings, update_strategy_params
from data.data_manager import DataManager
from strategies.strategy_manager import StrategyManager
from risk.risk_manager import RiskManager, PositionType
from backtesting.backtest_engine import BacktestEngine


@pytest.fixture
def settings():
    """Get settings for testing."""
    return get_settings()


@pytest.fixture
async def data_manager():
    """Create data manager for testing."""
    return DataManager()


@pytest.fixture
async def strategy_manager():
    """Create strategy manager for testing."""
    return StrategyManager()


@pytest.fixture
async def risk_manager():
    """Create risk manager for testing."""
    return RiskManager()


@pytest.fixture
async def backtest_engine():
    """Create backtest engine for testing."""
    return BacktestEngine()


class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_loading(self, settings):
        """Test that settings load correctly."""
        assert settings is not None
        assert hasattr(settings, 'strategy')
        assert hasattr(settings, 'risk')
        assert hasattr(settings, 'data')
    
    def test_strategy_params_update(self):
        """Test strategy parameter updates."""
        # Test updating parameters
        update_strategy_params({
            'z_score_threshold': 2.5,
            'position_size_pct': 0.03
        })
        
        # Verify updates
        params = get_settings().strategy
        assert params.z_score_threshold == 2.5
        assert params.position_size_pct == 0.03


class TestDataManager:
    """Test data management functionality."""
    
    @pytest.mark.asyncio
    async def test_data_manager_initialization(self, data_manager):
        """Test data manager initialization."""
        assert data_manager is not None
        assert hasattr(data_manager, 'settings')
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data(self, data_manager):
        """Test fetching historical data."""
        # Mock test - in real implementation, would test with actual data
        data = await data_manager.fetch_historical_data("AAPL", "1mo", "1h")
        # Should return DataFrame (empty if no data available)
        assert isinstance(data, pd.DataFrame)


class TestStrategyManager:
    """Test strategy management functionality."""
    
    @pytest.mark.asyncio
    async def test_strategy_manager_initialization(self, strategy_manager):
        """Test strategy manager initialization."""
        assert strategy_manager is not None
        assert hasattr(strategy_manager, 'strategies')
        assert len(strategy_manager.strategies) > 0
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, strategy_manager):
        """Test signal generation."""
        # Create mock data
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        mock_data = pd.DataFrame({
            'Open': np.random.randn(100) + 100,
            'High': np.random.randn(100) + 102,
            'Low': np.random.randn(100) + 98,
            'Close': np.random.randn(100) + 100,
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Calculate indicators
        mock_data['moving_avg'] = mock_data['Close'].rolling(window=20).mean()
        mock_data['std_dev'] = mock_data['Close'].rolling(window=20).std()
        mock_data['z_score'] = (mock_data['Close'] - mock_data['moving_avg']) / mock_data['std_dev']
        
        # Generate signals
        signals = await strategy_manager.generate_signals({"AAPL": mock_data})
        
        # Should return list of signals
        assert isinstance(signals, list)


class TestRiskManager:
    """Test risk management functionality."""
    
    @pytest.mark.asyncio
    async def test_risk_manager_initialization(self, risk_manager):
        """Test risk manager initialization."""
        assert risk_manager is not None
        assert hasattr(risk_manager, 'portfolio')
        assert risk_manager.portfolio.total_value == 100000.0
    
    def test_position_sizing(self, risk_manager):
        """Test position sizing calculation."""
        quantity = risk_manager.calculate_position_size(
            "AAPL", 150.0, 0.8, 100000.0
        )
        
        # Should return positive quantity
        assert quantity >= 0
    
    def test_stop_loss_take_profit(self, risk_manager):
        """Test stop loss and take profit calculation."""
        stop_loss, take_profit = risk_manager.calculate_stop_loss_take_profit(
            100.0, PositionType.LONG
        )
        
        # Stop loss should be below entry price for long positions
        assert stop_loss < 100.0
        # Take profit should be above entry price for long positions
        assert take_profit > 100.0
    
    def test_portfolio_update(self, risk_manager):
        """Test portfolio updates."""
        # Add a position
        success = risk_manager.add_position(
            "AAPL", PositionType.LONG, 10, 150.0, datetime.now()
        )
        assert success
        
        # Update portfolio
        risk_manager.update_portfolio("AAPL", 155.0, datetime.now())
        
        # Check portfolio summary
        summary = risk_manager.get_portfolio_summary()
        assert summary['num_positions'] == 1
        assert summary['total_pnl'] > 0  # Should have unrealized profit


class TestBacktestEngine:
    """Test backtesting functionality."""
    
    @pytest.mark.asyncio
    async def test_backtest_engine_initialization(self, backtest_engine):
        """Test backtest engine initialization."""
        assert backtest_engine is not None
        assert hasattr(backtest_engine, 'settings')
    
    @pytest.mark.asyncio
    async def test_backtest_simulation(self, backtest_engine):
        """Test backtest simulation."""
        # This is a basic test - in real implementation would test with actual data
        # For now, just test that the engine can be initialized
        await backtest_engine.initialize()
        assert backtest_engine.data_manager is not None
        assert backtest_engine.strategy_manager is not None
        assert backtest_engine.risk_manager is not None


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test the full trading bot workflow."""
        # Initialize components
        data_manager = DataManager()
        strategy_manager = StrategyManager()
        risk_manager = RiskManager()
        
        # Test that all components can work together
        assert data_manager is not None
        assert strategy_manager is not None
        assert risk_manager is not None
        
        # Test parameter updates
        update_strategy_params({
            'z_score_threshold': 2.0,
            'position_size_pct': 0.02
        })
        
        # Verify parameters were updated
        settings = get_settings()
        assert settings.strategy.z_score_threshold == 2.0
        assert settings.strategy.position_size_pct == 0.02


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"]) 