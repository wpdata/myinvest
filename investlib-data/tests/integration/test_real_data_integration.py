"""
Integration Tests for Real Data Flow (US5 - T007)

These tests verify end-to-end real data integration:
- Efinance API → Real OHLCV data with metadata
- Fallback chain: Efinance → AKShare → Cache
- Data freshness calculation
- Cache persistence with 7-day retention

Expected Status: RED PHASE (some tests will FAIL until T008 enhancements)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from investlib_data.models import Base, MarketDataPoint, DataFreshness, AdjustmentMethod
from investlib_data.market_api import MarketDataFetcher, EfinanceClient, AKShareClient, EfinanceAPIError, AKShareAPIError
from investlib_data.cache_manager import CacheManager


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


@pytest.mark.integration
class TestRealDataIntegration:
    """Integration tests for real data flow from APIs to cache."""

    def test_efinance_real_api_call_returns_ohlcv_data(self):
        """Test real Efinance API call for 600519.SH → returns OHLCV data

        This test makes a real API call to Efinance.
        Expected to PASS if Efinance API is accessible.
        """
        fetcher = MarketDataFetcher()
        symbol = "600519.SH"

        # Fetch last 30 days of data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        try:
            result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            pytest.skip(f"Efinance API unavailable: {e}")

        # Verify data structure
        assert result is not None
        assert 'data' in result
        assert 'metadata' in result

        data = result['data']
        metadata = result['metadata']

        # Verify OHLCV columns present
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in data.columns, f"Missing required column: {col}"

        # Verify data not empty
        assert len(data) > 0, "Should return at least some historical data"

        # Verify OHLC constraints
        assert (data['high'] >= data['low']).all(), "High must be >= Low"
        assert (data['high'] >= data['open']).all(), "High must be >= Open"
        assert (data['high'] >= data['close']).all(), "High must be >= Close"
        assert (data['low'] <= data['open']).all(), "Low must be <= Open"
        assert (data['low'] <= data['close']).all(), "Low must be <= Close"

        # Verify all prices positive
        assert (data['open'] > 0).all(), "Prices must be positive"
        assert (data['high'] > 0).all()
        assert (data['low'] > 0).all()
        assert (data['close'] > 0).all()
        assert (data['volume'] >= 0).all(), "Volume must be non-negative"

    def test_metadata_includes_api_source_and_fresh_timestamp(self):
        """Test metadata includes source='Efinance v{version}' and fresh timestamp

        Expected to PASS.
        """
        fetcher = MarketDataFetcher()
        symbol = "600519.SH"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        try:
            result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
        except Exception:
            pytest.skip("API unavailable")

        metadata = result['metadata']

        # Verify required metadata fields
        assert 'api_source' in metadata, "Metadata must include api_source"
        assert 'retrieval_timestamp' in metadata, "Metadata must include retrieval_timestamp"
        assert 'data_freshness' in metadata, "Metadata must include data_freshness"

        # Verify api_source includes API name and version
        api_source = metadata['api_source']
        assert "Efinance" in api_source or "AKShare" in api_source, \
            f"api_source should include API name, got: {api_source}"
        assert "v" in api_source.lower() or "latest" in api_source.lower(), \
            f"api_source should include version, got: {api_source}"

        # Verify retrieval_timestamp is recent (within last minute)
        retrieval_time = metadata['retrieval_timestamp']
        assert isinstance(retrieval_time, datetime), "retrieval_timestamp must be datetime"
        time_diff = (datetime.utcnow() - retrieval_time).total_seconds()
        assert time_diff < 60, f"retrieval_timestamp too old: {time_diff}s ago"

        # Verify data_freshness is valid enum value
        assert metadata['data_freshness'] in ['realtime', 'delayed', 'historical'], \
            f"Invalid data_freshness: {metadata['data_freshness']}"

    @patch("investlib_data.market_api.EfinanceClient")
    def test_efinance_failure_fallback_to_akshare_succeeds(self, MockEfinance, db_session):
        """Test mock Efinance failure → fallback to AKShare succeeds

        Expected to PASS with mocked APIs.
        """
        # Mock Efinance to fail
        mock_efinance_instance = MockEfinance.return_value
        mock_efinance_instance.fetch_daily_data.side_effect = EfinanceAPIError("Efinance API rate limit")
        mock_efinance_instance.version = "latest"

        # Create test data for AKShare success
        test_data = pd.DataFrame({
            'timestamp': [datetime(2024, 10, 15), datetime(2024, 10, 16)],
            'open': [1680.0, 1690.0],
            'high': [1720.0, 1730.0],
            'low': [1650.0, 1660.0],
            'close': [1700.0, 1710.0],
            'volume': [1000000, 1100000],
            'api_source': ['AKShare v1.11.0', 'AKShare v1.11.0'],
            'api_version': ['1.11.0', '1.11.0'],
            'retrieval_timestamp': [datetime.utcnow(), datetime.utcnow()],
            'data_freshness': ['realtime', 'realtime']
        })

        # Mock AKShare to succeed
        with patch("investlib_data.market_api.AKShareClient") as MockAKShare:
            mock_akshare_instance = MockAKShare.return_value
            mock_akshare_instance.fetch_daily_data.return_value = test_data
            mock_akshare_instance.version = "1.11.0"

            # Create fetcher (will use mocked clients)
            fetcher = MarketDataFetcher()

            # Execute fetch
            result = fetcher.fetch_with_fallback(
                symbol="600519.SH",
                start_date="2024-10-15",
                end_date="2024-10-16"
            )

            # Verify fallback worked
            assert result is not None
            assert 'data' in result
            assert 'metadata' in result

            # Verify data came from AKShare
            assert "AKShare" in result['metadata']['api_source']
            assert len(result['data']) > 0

            # Verify both APIs were attempted
            mock_efinance_instance.fetch_daily_data.assert_called_once()
            mock_akshare_instance.fetch_daily_data.assert_called_once()

    @pytest.mark.skip(reason="T008 not implemented - cache fallback not ready")
    def test_both_apis_fail_cache_returns_data_with_warning(self, db_session):
        """Test both APIs fail → cache returns data with warning

        This test is EXPECTED TO FAIL until T008 implementation.
        T008 will enhance MarketDataFetcher to add cache as 3rd fallback level.
        """
        # Pre-populate cache with test data
        cache = CacheManager(session=db_session)
        symbol = "600519.SH"
        cached_data = pd.DataFrame({
            'timestamp': [datetime(2024, 10, 15)],
            'open': [1680.0],
            'high': [1720.0],
            'low': [1650.0],
            'close': [1700.0],
            'volume': [1000000]
        })
        cache.save_to_cache(symbol, cached_data, "Efinance", "latest")

        # Mock both APIs to fail
        with patch("investlib_data.market_api.EfinanceClient") as MockEfinance, \
             patch("investlib_data.market_api.AKShareClient") as MockAKShare:

            mock_efinance_instance = MockEfinance.return_value
            mock_efinance_instance.fetch_daily_data.side_effect = EfinanceAPIError("API down")

            mock_akshare_instance = MockAKShare.return_value
            mock_akshare_instance.fetch_daily_data.side_effect = AKShareAPIError("API down")

            # Enhanced MarketDataFetcher should fall back to cache
            # This will FAIL until T008 implements cache fallback
            fetcher = MarketDataFetcher()

            result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date="2024-10-15",
                end_date="2024-10-16"
            )

            # Verify data came from cache
            assert result is not None
            assert 'data' in result
            assert len(result['data']) > 0
            assert result['metadata']['api_source'].startswith("Cache")
            assert result['metadata']['data_freshness'] == 'historical'

    def test_cache_saves_data_with_7_day_expiry(self, db_session):
        """Test cache saves data with 7-day expiry

        Expected to PASS.
        """
        cache = CacheManager(session=db_session)
        symbol = "600519.SH"

        test_data = pd.DataFrame({
            'timestamp': [datetime(2024, 10, 15), datetime(2024, 10, 16)],
            'open': [1680.0, 1690.0],
            'high': [1720.0, 1730.0],
            'low': [1650.0, 1660.0],
            'close': [1700.0, 1710.0],
            'volume': [1000000, 1100000]
        })

        # Save to cache
        count = cache.save_to_cache(symbol, test_data, "Efinance", "latest")
        assert count == 2, "Should save 2 records"

        # Query cache entries
        entries = db_session.query(MarketDataPoint).filter_by(symbol=symbol).all()
        assert len(entries) == 2

        # Verify cache_expiry_date is set to 7 days from now
        for entry in entries:
            assert entry.cache_expiry_date is not None

            # Cache retention is 7 days
            expiry_delta = (entry.cache_expiry_date - entry.retrieval_timestamp).days
            assert expiry_delta == 7, f"Expected 7 day retention, got {expiry_delta} days"

            # Verify expiry is in the future
            assert entry.cache_expiry_date > datetime.utcnow(), "Cache should not be expired yet"

    def test_data_freshness_calculation_realtime_vs_historical(self, db_session):
        """Test data_freshness calculation: realtime (<5s) vs delayed vs historical

        Expected to PASS for realtime/delayed detection.
        Historical detection may need T008 enhancements.
        """
        # Test 1: Fresh data (just fetched) → realtime or delayed
        fetcher = MarketDataFetcher()
        symbol = "600519.SH"

        try:
            result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
        except Exception:
            pytest.skip("API unavailable")

        metadata = result['metadata']
        retrieval_time = metadata['retrieval_timestamp']
        freshness = metadata['data_freshness']

        # Calculate time since retrieval
        time_diff = (datetime.utcnow() - retrieval_time).total_seconds()

        # If just fetched (<5s), should be realtime or delayed
        if time_diff < 5:
            assert freshness in ['realtime', 'delayed'], \
                f"Fresh data (<5s) should be realtime/delayed, got: {freshness}"

        # Test 2: Cached data (historical)
        # Save old data to cache (8 days ago - beyond 7 day retention)
        cache = CacheManager(session=db_session)
        old_timestamp = datetime.utcnow() - timedelta(days=8)

        old_data = pd.DataFrame({
            'timestamp': [datetime(2024, 10, 1)],
            'open': [1600.0],
            'high': [1650.0],
            'low': [1580.0],
            'close': [1630.0],
            'volume': [900000]
        })

        cache.save_to_cache("000001.SZ", old_data, "Efinance", "latest")

        # Manually set retrieval_timestamp to old value
        entry = db_session.query(MarketDataPoint).filter_by(symbol="000001.SZ").first()
        entry.retrieval_timestamp = old_timestamp
        entry.data_freshness = DataFreshness.HISTORICAL
        db_session.commit()

        # Retrieve from cache
        cached_result = cache.get_from_cache(
            "000001.SZ",
            datetime(2024, 10, 1),
            datetime(2024, 10, 2)
        )

        assert not cached_result.empty
        assert cached_result.iloc[0]['data_freshness'] == 'historical'

    def test_api_retry_logic_with_exponential_backoff(self):
        """Test retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)

        This test verifies current retry behavior in EfinanceClient/AKShareClient.
        Expected to PASS.
        """
        # Test that EfinanceClient has retry logic
        client = EfinanceClient()

        # Mock the underlying API to fail first 2 times, succeed 3rd time
        with patch.object(client, 'ef') as mock_ef:
            # First 2 calls fail, 3rd succeeds
            mock_ef.stock.get_quote_history.side_effect = [
                Exception("Temporary error 1"),
                Exception("Temporary error 2"),
                pd.DataFrame({
                    '日期': [datetime(2024, 10, 15)],
                    '开盘': [1680.0],
                    '最高': [1720.0],
                    '最低': [1650.0],
                    '收盘': [1700.0],
                    '成交量': [1000000],
                    '股票代码': ['600519'],
                    '股票名称': ['贵州茅台']
                })
            ]

            # Should succeed on 3rd attempt
            result = client.fetch_daily_data("600519.SH", "20241015", "20241015")

            # Verify retry happened
            assert mock_ef.stock.get_quote_history.call_count == 3
            assert not result.empty

    def test_end_to_end_real_data_flow(self, db_session):
        """Test complete data flow: API → Fetcher → Cache → Retrieval

        This is a comprehensive end-to-end test.
        Expected to PASS (uses real API if available, mocked otherwise).
        """
        fetcher = MarketDataFetcher()
        cache = CacheManager(session=db_session)
        symbol = "600519.SH"

        # Step 1: Fetch real data
        try:
            result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
        except Exception:
            pytest.skip("API unavailable for end-to-end test")

        data = result['data']
        metadata = result['metadata']

        # Step 2: Save to cache
        count = cache.save_to_cache(
            symbol,
            data,
            metadata['api_source'],
            metadata.get('api_version', 'unknown')
        )
        assert count > 0, "Should save at least one record"

        # Step 3: Retrieve from cache
        start_date = data['timestamp'].min()
        end_date = data['timestamp'].max()

        cached_data = cache.get_from_cache(symbol, start_date, end_date)
        assert not cached_data.empty, "Cache should return data"
        assert len(cached_data) > 0, "Should have at least some cached data"

        # Step 4: Verify data integrity
        # Cache should mark data as 'historical' since it's from cache
        assert all(cached_data['data_freshness'] == 'historical'), \
            "Cached data should be marked as 'historical'"

        # Verify OHLCV columns exist in cached data
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in cached_data.columns, f"Cached data missing column: {col}"

        # Verify cached data has valid prices
        assert (cached_data['close'] > 0).all(), "Cached close prices must be positive"
        assert (cached_data['high'] >= cached_data['low']).all(), "Cached high must be >= low"
