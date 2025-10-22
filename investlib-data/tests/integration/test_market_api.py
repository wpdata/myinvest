"""Integration tests for market data APIs and cache manager."""

import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from investlib_data.market_api import EfinanceClient, AKShareClient, MarketDataFetcher, EfinanceAPIError
from investlib_data.cache_manager import CacheManager
from investlib_data.models import Base, DataFreshness, AdjustmentMethod

@pytest.fixture(scope="module")
def engine():
    """Create an in-memory SQLite database engine for tests."""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test function."""
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.mark.slow
class TestMarketAPIs:
    """Test Efinance and AKShare clients with real API calls."""

    def test_efinance_client_fetches_real_data(self):
        """Test EfinanceClient fetches real data for a known symbol."""
        client = EfinanceClient()
        df = client.fetch_daily_data(symbol="600519.SH", start_date="20230101", end_date="20230131")

        assert not df.empty
        assert "timestamp" in df.columns
        assert "api_source" in df.columns
        assert "Efinance" in df.iloc[0]["api_source"]

    def test_akshare_client_fetches_real_data(self):
        """Test AKShareClient fetches real data."""
        client = AKShareClient()
        df = client.fetch_daily_data(symbol="600519.SH", start_date="20230101", end_date="20230131")

        assert not df.empty
        assert "timestamp" in df.columns
        assert "api_source" in df.columns
        assert "AKShare" in df.iloc[0]["api_source"]

@patch("investlib_data.market_api.EfinanceClient")
@patch("investlib_data.market_api.AKShareClient")
def test_fetcher_fallback_logic(MockAKShare, MockEfinance):
    """Test MarketDataFetcher fallback from Efinance to AKShare."""
    # Arrange: Efinance fails, AKShare succeeds
    mock_efinance_instance = MockEfinance.return_value
    mock_efinance_instance.fetch_daily_data.side_effect = EfinanceAPIError("Efinance failed")
    mock_efinance_instance.version = "latest"

    mock_akshare_instance = MockAKShare.return_value
    mock_akshare_instance.fetch_daily_data.return_value = pd.DataFrame({'close': [100]})
    mock_akshare_instance.version = "1.11.0"

    fetcher = MarketDataFetcher()

    # Act
    result = fetcher.fetch_with_fallback(symbol="600519.SH")

    # Assert
    assert not result['data'].empty
    assert result['metadata']['api_source'] == f"AKShare v{mock_akshare_instance.version}"
    mock_efinance_instance.fetch_daily_data.assert_called_once()
    mock_akshare_instance.fetch_daily_data.assert_called_once()

class TestCacheManager:
    """Test the CacheManager functionality."""

    def test_save_and_get_from_cache(self, db_session):
        """Test saving to and retrieving from the cache."""
        cache = CacheManager(session=db_session)
        symbol = "600519.SH"
        test_data = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1)],
            'open': [1500], 'high': [1550], 'low': [1490], 'close': [1520], 'volume': [10000]
        })

        # Save to cache
        count = cache.save_to_cache(symbol, test_data, "TestAPI", "1.0")
        assert count == 1

        # Retrieve from cache
        cached_df = cache.get_from_cache(symbol, datetime(2023, 1, 1), datetime(2023, 1, 2))
        assert not cached_df.empty
        assert cached_df.iloc[0]['close'] == 1520
        assert cached_df.iloc[0]['data_freshness'] == 'historical'

    def test_cache_expiry(self, db_session):
        """Test that expired cache data is not retrieved."""
        cache = CacheManager(session=db_session)
        symbol = "000001.SZ"
        test_data = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1)],
            'open': [10], 'high': [11], 'low': [9], 'close': [10.5], 'volume': [20000]
        })

        # Save to cache
        cache.save_to_cache(symbol, test_data, "TestAPI", "1.0")

        # Manually expire the data
        from investlib_data.models import MarketDataPoint
        entry = db_session.query(MarketDataPoint).first()
        entry.cache_expiry_date = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        # Try to retrieve expired data
        cached_df = cache.get_from_cache(symbol, datetime(2023, 1, 1), datetime(2023, 1, 2))
        assert cached_df.empty

    def test_cleanup_expired(self, db_session):
        """Test the cleanup_expired method."""
        cache = CacheManager(session=db_session)
        # Add one valid entry
        cache.save_to_cache("600519.SH", pd.DataFrame({'timestamp': [datetime.now()], 'open': [1], 'high': [1], 'low': [1], 'close': [1], 'volume': [1]}), "Test", "1.0")
        # Add one expired entry
        from investlib_data.models import MarketDataPoint
        expired_entry = MarketDataPoint(symbol="000001.SZ", timestamp=datetime(2023,1,1), open_price=1, high_price=1, low_price=1, close_price=1, volume=1, api_source="Test", api_version="1.0", cache_expiry_date=datetime.utcnow() - timedelta(days=1), data_freshness=DataFreshness.HISTORICAL, adjustment_method=AdjustmentMethod.UNADJUSTED)
        db_session.add(expired_entry)
        db_session.commit()

        assert db_session.query(MarketDataPoint).count() == 2

        deleted_count = cache.cleanup_expired()
        assert deleted_count == 1
        assert db_session.query(MarketDataPoint).count() == 1
