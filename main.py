"""
Main trading bot application with FastAPI integration, dashboard, and parameter optimization.
All parameters are easily tweakable for better results.
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from config import get_settings, update_strategy_params, get_strategy_params
from data.data_manager import get_data_manager
from strategies.strategy_manager import get_strategy_manager
from risk.risk_manager import get_risk_manager
from backtesting.backtest_engine import get_backtest_engine

# Configure structured logging
logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Mean Reversion Trading Bot",
    description="A comprehensive trading bot with mean reversion strategy",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class StrategyParams(BaseModel):
    """Strategy parameters for API updates."""
    lookback_window: Optional[int] = None
    threshold: Optional[float] = None
    position_size_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    enable_dynamic_risk: Optional[bool] = None
    risk_multiplier: Optional[float] = None


class BacktestRequest(BaseModel):
    """Backtest request model."""
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0


class TradingBot:
    """Main trading bot class."""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_manager = None
        self.strategy_manager = None
        self.risk_manager = None
        self.backtest_engine = None
        self.is_running = False
        self.trading_task = None
    
    async def initialize(self):
        """Initialize all components."""
        try:
            self.data_manager = await get_data_manager()
            self.strategy_manager = await get_strategy_manager()
            self.risk_manager = await get_risk_manager()
            self.backtest_engine = await get_backtest_engine()
            
            logger.info("Trading bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing trading bot: {e}")
            raise
    
    async def start_trading(self):
        """Start live trading."""
        if self.is_running:
            logger.warning("Trading bot is already running")
            return
        
        try:
            self.is_running = True
            self.trading_task = asyncio.create_task(self._trading_loop())
            logger.info("Trading bot started")
            
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            self.is_running = False
    
    async def stop_trading(self):
        """Stop live trading."""
        if not self.is_running:
            logger.warning("Trading bot is not running")
            return
        
        try:
            self.is_running = False
            if self.trading_task:
                self.trading_task.cancel()
                try:
                    await self.trading_task
                except asyncio.CancelledError:
                    pass
                self.trading_task = None
            
            logger.info("Trading bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading bot: {e}")
    
    async def _trading_loop(self):
        """Main trading loop."""
        while self.is_running:
            try:
                # Fetch latest data
                symbols = self.settings.data.symbols
                data_dict = await self.data_manager.get_multiple_symbols_data(symbols)
                
                # Calculate indicators
                for symbol, data in data_dict.items():
                    if not data.empty:
                        data = await self.data_manager.calculate_indicators(data, symbol)
                        data_dict[symbol] = data
                
                # Generate signals
                signals = await self.strategy_manager.generate_signals(data_dict)
                
                # Execute signals
                for signal in signals:
                    await self._execute_live_signal(signal)
                
                # Update portfolio
                for symbol, data in data_dict.items():
                    if not data.empty:
                        latest_price = data.iloc[-1]['Close']
                        self.risk_manager.update_portfolio(symbol, latest_price, datetime.now())
                
                # Check for stop loss/take profit
                await self._check_live_exits(data_dict)
                
                # Wait for next update
                await asyncio.sleep(self.settings.data.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _execute_live_signal(self, signal):
        """Execute a live trading signal."""
        try:
            # For now, just log the signal
            # In production, this would interface with broker APIs
            logger.info(f"Live signal: {signal.signal_type} {signal.symbol} @ {signal.price}")
            
            # TODO: Implement actual order execution
            # This would involve:
            # 1. Calculating position size
            # 2. Checking risk limits
            # 3. Placing orders via broker API
            # 4. Updating portfolio
            
        except Exception as e:
            logger.error(f"Error executing live signal: {e}")
    
    async def _check_live_exits(self, data_dict):
        """Check for live stop loss/take profit exits."""
        try:
            for symbol, data in data_dict.items():
                if not data.empty:
                    current_price = data.iloc[-1]['Close']
                    exit_reason = self.risk_manager.check_stop_loss_take_profit(symbol, current_price)
                    
                    if exit_reason:
                        logger.info(f"Live exit signal: {symbol} due to {exit_reason}")
                        # TODO: Implement actual position closing
                        
        except Exception as e:
            logger.error(f"Error checking live exits: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get trading bot status."""
        return {
            'is_running': self.is_running,
            'portfolio_summary': self.risk_manager.get_portfolio_summary(),
            'strategy_performance': self.strategy_manager.get_strategy_performance(),
            'cache_info': self.data_manager.get_cache_info() if self.data_manager else {}
        }


# Global trading bot instance
trading_bot = TradingBot()


# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Mean Reversion Trading Bot", "version": "1.0.0"}


@app.get("/status")
async def get_status():
    """Get trading bot status."""
    return trading_bot.get_status()


@app.post("/start")
async def start_trading():
    """Start live trading."""
    try:
        await trading_bot.initialize()
        await trading_bot.start_trading()
        return {"message": "Trading bot started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop")
async def stop_trading():
    """Stop live trading."""
    try:
        await trading_bot.stop_trading()
        return {"message": "Trading bot stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/strategy/params")
async def get_strategy_parameters():
    """Get current strategy parameters."""
    return get_strategy_params()


@app.post("/strategy/params")
async def update_strategy_parameters(params: StrategyParams):
    """Update strategy parameters."""
    try:
        # Convert to dict and remove None values
        param_dict = {k: v for k, v in params.dict().items() if v is not None}
        update_strategy_params(param_dict)
        return {"message": "Strategy parameters updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest simulation."""
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
        
        # Run backtest
        results = await trading_bot.backtest_engine.run_backtest(
            request.symbols,
            start_date,
            end_date,
            request.initial_capital
        )
        
        return {
            "total_return": results.total_return,
            "total_return_pct": results.total_return_pct,
            "sharpe_ratio": results.sharpe_ratio,
            "max_drawdown_pct": results.max_drawdown_pct,
            "win_rate": results.win_rate,
            "profit_factor": results.profit_factor,
            "total_trades": results.total_trades
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio")
async def get_portfolio():
    """Get portfolio summary."""
    return trading_bot.risk_manager.get_portfolio_summary()


@app.get("/trades")
async def get_trade_history(symbol: Optional[str] = None):
    """Get trade history."""
    return trading_bot.risk_manager.get_trade_history(symbol)


# Streamlit Dashboard
def create_dashboard():
    """Create Streamlit dashboard."""
    st.set_page_config(
        page_title="Trading Bot Dashboard",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("Mean Reversion Trading Bot Dashboard")
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # Strategy selection
    strategy_type = st.sidebar.selectbox(
        "Strategy Type",
        ["mean_reversion"]
    )
    
    # Parameter sliders
    st.sidebar.subheader("Strategy Parameters")
    
    lookback_window = st.sidebar.slider("Lookback Window", 5, 50, 20)
    threshold = st.sidebar.slider("Threshold", 0.005, 0.05, 0.01, 0.001)
    position_size_pct = st.sidebar.slider("Position Size %", 0.01, 0.10, 0.02, 0.01)
    stop_loss_pct = st.sidebar.slider("Stop Loss %", 0.01, 0.20, 0.05, 0.01)
    take_profit_pct = st.sidebar.slider("Take Profit %", 0.05, 0.30, 0.10, 0.01)
    
    # Update parameters
    if st.sidebar.button("Update Parameters"):
        try:
            update_strategy_params({
                'lookback_window': lookback_window,
                'threshold': threshold,
                'position_size_pct': position_size_pct,
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct
            })
            st.sidebar.success("Parameters updated!")
        except Exception as e:
            st.sidebar.error(f"Error updating parameters: {e}")
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Portfolio Summary")
        portfolio = trading_bot.risk_manager.get_portfolio_summary()
        
        if portfolio:
            st.metric("Total Value", f"${portfolio['total_value']:,.2f}")
            st.metric("Total P&L", f"${portfolio['total_pnl']:,.2f}")
            st.metric("Total P&L %", f"{portfolio['total_pnl_pct']:.2%}")
            st.metric("Max Drawdown", f"{portfolio['max_drawdown']:.2%}")
            st.metric("Sharpe Ratio", f"{portfolio['sharpe_ratio']:.2f}")
            st.metric("Number of Positions", portfolio['num_positions'])
    
    with col2:
        st.subheader("Strategy Performance")
        performance = trading_bot.strategy_manager.get_strategy_performance()
        
        if performance:
            st.metric("Total Signals", performance['total_signals'])
            st.metric("Buy Signals", performance['buy_signals'])
            st.metric("Sell Signals", performance['sell_signals'])
            st.metric("Avg Confidence", f"{performance['avg_confidence']:.2f}")
    
    # Backtest section
    st.subheader("Backtest")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbols = st.multiselect(
            "Symbols",
            ["EURAUD=X", "EURCAD=X"],
            default=["EURAUD=X", "EURCAD=X"]
        )
    
    with col2:
        start_date = st.date_input("Start Date", value=datetime(2023, 1, 1))
    
    with col3:
        end_date = st.date_input("End Date", value=datetime(2023, 12, 31))
    
    if st.button("Run Backtest"):
        if symbols:
            try:
                with st.spinner("Running backtest..."):
                    results = asyncio.run(trading_bot.backtest_engine.run_backtest(
                        symbols,
                        datetime.combine(start_date, datetime.min.time()),
                        datetime.combine(end_date, datetime.max.time())
                    ))
                
                # Display results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"${results.total_return:,.2f}")
                    st.metric("Total Return %", f"{results.total_return_pct:.2%}")
                
                with col2:
                    st.metric("Sharpe Ratio", f"{results.sharpe_ratio:.2f}")
                    st.metric("Max Drawdown", f"{results.max_drawdown_pct:.2%}")
                
                with col3:
                    st.metric("Win Rate", f"{results.win_rate:.2%}")
                    st.metric("Profit Factor", f"{results.profit_factor:.2f}")
                
                with col4:
                    st.metric("Total Trades", results.total_trades)
                    st.metric("Winning Trades", results.winning_trades)
                
                # Plot equity curve
                if not results.equity_curve.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=results.equity_curve.index,
                        y=results.equity_curve['total_value'],
                        mode='lines',
                        name='Portfolio Value'
                    ))
                    fig.update_layout(
                        title="Equity Curve",
                        xaxis_title="Date",
                        yaxis_title="Portfolio Value ($)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error running backtest: {e}")
        else:
            st.warning("Please select at least one symbol")


def run_streamlit():
    """Run Streamlit dashboard."""
    import streamlit.web.cli as stcli
    import sys
    
    sys.argv = ["streamlit", "run", "main.py", "--server.port", "8501"]
    sys.exit(stcli.main())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        # Run Streamlit dashboard
        create_dashboard()
    else:
        # Run FastAPI server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        ) 