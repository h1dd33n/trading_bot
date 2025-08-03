"""
Data management module for fetching, storing, and processing market data.
Enhanced with caching, real-time updates, and multiple data sources.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Float, DateTime, Integer, Index
import structlog
from config import get_settings, DataSource

# Configure structured logging
logger = structlog.get_logger()

Base = declarative_base()


class PriceData(Base):
    """Database model for price data."""
    __tablename__ = "price_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )


class NormalizedData(Base):
    """Database model for normalized/calculated data."""
    __tablename__ = "normalized_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    moving_avg = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    bollinger_upper = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    bollinger_middle = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_norm_symbol_timestamp', 'symbol', 'timestamp'),
    )


class DataManager:
    """Enhanced data manager with caching, real-time updates, and multiple sources."""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.Session = None
        self._cache = {}
        self._last_update = {}
        self._update_task = None
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database connection."""
        try:
            db_config = self.settings.database
            connection_string = (
                f"postgresql://{db_config.username}:{db_config.password}@"
                f"{db_config.host}:{db_config.port}/{db_config.database}"
            )
            
            self.engine = create_engine(
                connection_string,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
                echo=self.settings.debug
            )
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def fetch_historical_data(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Fetch historical data from yfinance with caching."""
        cache_key = f"{symbol}_{period}_{interval}"
        
        # Check cache first
        if cache_key in self._cache:
            last_update = self._last_update.get(cache_key)
            if last_update and (datetime.now() - last_update).seconds < 300:  # 5 min cache
                logger.debug(f"Using cached data for {symbol}")
                return self._cache[cache_key]
        
        try:
            logger.info(f"Fetching historical data for {symbol}")
            ticker = yf.Ticker(symbol)
            
            if start_date and end_date:
                # Use custom date range
                data = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                # Use period
                data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Store in cache
            self._cache[cache_key] = data
            self._last_update[cache_key] = datetime.now()
            
            # Store in database
            await self._store_data_in_db(symbol, data)
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _store_data_in_db(self, symbol: str, data: pd.DataFrame):
        """Store data in database."""
        try:
            session = self.Session()
            
            for timestamp, row in data.iterrows():
                # Convert timestamp to timezone-naive datetime
                if hasattr(timestamp, 'tz_localize'):
                    timestamp = timestamp.tz_localize(None)
                elif hasattr(timestamp, 'replace'):
                    timestamp = timestamp.replace(tzinfo=None)
                
                # Check if data already exists
                existing = session.query(PriceData).filter_by(
                    symbol=symbol, timestamp=timestamp
                ).first()
                
                if not existing:
                    # Convert numpy types to Python native types
                    price_data = PriceData(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume'])
                    )
                    session.add(price_data)
            
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error storing data in database: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
    
    async def get_latest_data(self, symbol: str, lookback_days: int = 30) -> pd.DataFrame:
        """Get latest data from database or fetch if needed."""
        try:
            session = self.Session()
            
            # Query database for recent data
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            db_data = session.query(PriceData).filter(
                PriceData.symbol == symbol,
                PriceData.timestamp >= cutoff_date
            ).order_by(PriceData.timestamp).all()
            
            if db_data:
                # Convert to DataFrame
                data = pd.DataFrame([
                    {
                        'Open': row.open,
                        'High': row.high,
                        'Low': row.low,
                        'Close': row.close,
                        'Volume': row.volume
                    }
                    for row in db_data
                ], index=[row.timestamp for row in db_data])
                
                session.close()
                return data
            
            session.close()
            
            # If no data in DB, fetch from yfinance
            return await self.fetch_historical_data(symbol, f"{lookback_days}d", "1h")
            
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def calculate_indicators(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Calculate technical indicators for the data."""
        if data.empty:
            return data
        
        try:
            # Calculate moving averages
            lookback = self.settings.strategy.lookback_window
            data['moving_avg'] = data['Close'].rolling(window=lookback).mean()
            data['std_dev'] = data['Close'].rolling(window=lookback).std()
            
            # Calculate z-score
            data['z_score'] = (data['Close'] - data['moving_avg']) / data['std_dev']
            
            # Calculate RSI
            data['rsi'] = self._calculate_rsi(data['Close'], self.settings.strategy.rsi_period)
            
            # Calculate Bollinger Bands
            bb_period = self.settings.strategy.bollinger_period
            bb_std = self.settings.strategy.bollinger_std
            
            bb_middle = data['Close'].rolling(window=bb_period).mean()
            bb_std_dev = data['Close'].rolling(window=bb_period).std()
            
            data['bollinger_upper'] = bb_middle + (bb_std_dev * bb_std)
            data['bollinger_lower'] = bb_middle - (bb_std_dev * bb_std)
            data['bollinger_middle'] = bb_middle
            
            # Store normalized data in database
            await self._store_normalized_data(symbol, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series(index=prices.index)
    
    async def _store_normalized_data(self, symbol: str, data: pd.DataFrame):
        """Store normalized data in database."""
        try:
            session = self.Session()
            
            for timestamp, row in data.iterrows():
                if pd.isna(row['moving_avg']):
                    continue
                
                # Convert timestamp to timezone-naive datetime
                if hasattr(timestamp, 'tz_localize'):
                    timestamp = timestamp.tz_localize(None)
                elif hasattr(timestamp, 'replace'):
                    timestamp = timestamp.replace(tzinfo=None)
                
                # Check if normalized data already exists
                existing = session.query(NormalizedData).filter_by(
                    symbol=symbol, timestamp=timestamp
                ).first()
                
                if not existing:
                    # Convert numpy types to Python native types
                    normalized_data = NormalizedData(
                        symbol=symbol,
                        timestamp=timestamp,
                        moving_avg=float(row['moving_avg']) if not pd.isna(row['moving_avg']) else None,
                        std_dev=float(row['std_dev']) if not pd.isna(row['std_dev']) else None,
                        z_score=float(row['z_score']) if not pd.isna(row['z_score']) else None,
                        rsi=float(row['rsi']) if not pd.isna(row['rsi']) else None,
                        bollinger_upper=float(row['bollinger_upper']) if not pd.isna(row['bollinger_upper']) else None,
                        bollinger_lower=float(row['bollinger_lower']) if not pd.isna(row['bollinger_lower']) else None,
                        bollinger_middle=float(row['bollinger_middle']) if not pd.isna(row['bollinger_middle']) else None
                    )
                    session.add(normalized_data)
            
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"Error storing normalized data: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
    
    async def get_multiple_symbols_data(
        self, 
        symbols: List[str], 
        lookback_days: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols concurrently."""
        tasks = []
        for symbol in symbols:
            task = self.get_latest_data(symbol, lookback_days)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching data for {symbol}: {result}")
                data_dict[symbol] = pd.DataFrame()
            else:
                # Calculate indicators for the data
                if not result.empty:
                    result = await self.calculate_indicators(result, symbol)
                data_dict[symbol] = result
        
        return data_dict
    
    async def start_real_time_updates(self):
        """Start real-time data updates."""
        if self._update_task:
            return
        
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Started real-time data updates")
    
    async def stop_real_time_updates(self):
        """Stop real-time data updates."""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
            logger.info("Stopped real-time data updates")
    
    async def _update_loop(self):
        """Main update loop for real-time data."""
        while True:
            try:
                for symbol in self.settings.data.symbols:
                    # Fetch latest data
                    data = await self.fetch_historical_data(symbol, "1d", "1m")
                    if not data.empty:
                        # Calculate indicators
                        data = await self.calculate_indicators(data, symbol)
                        
                        # Update cache
                        cache_key = f"{symbol}_1d_1m"
                        self._cache[cache_key] = data
                        self._last_update[cache_key] = datetime.now()
                
                # Wait for next update
                await asyncio.sleep(self.settings.data.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        return {
            "cache_size": len(self._cache),
            "last_updates": self._last_update,
            "symbols": self.settings.data.symbols
        }
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache.clear()
        self._last_update.clear()
        logger.info("Data cache cleared")


# Global data manager instance
data_manager = DataManager()


async def get_data_manager() -> DataManager:
    """Get the global data manager instance."""
    return data_manager


if __name__ == "__main__":
    # Test the data manager
    async def test():
        dm = DataManager()
        data = await dm.fetch_historical_data("AAPL", "1mo", "1h")
        print(f"Fetched {len(data)} records for AAPL")
        
        if not data.empty:
            data = await dm.calculate_indicators(data, "AAPL")
            print("Calculated indicators")
            print(data.tail())
    
    asyncio.run(test()) 