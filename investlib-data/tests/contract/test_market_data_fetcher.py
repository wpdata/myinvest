"""
Contract Tests for MarketDataFetcher (US5 - T006)

These tests verify the contract/interface of MarketDataFetcher for V0.2:
- fetch_with_fallback() returns dict with data + metadata
- Metadata includes required fields
- Fallback chain: Efinance → AKShare → Cache
- Retry logic with exponential backoff
- Data freshness calculation

Expected Status: RED PHASE (tests should FAIL until T008 implementation)
"""

import pytest
from datetime import datetime, timedelta
from investlib_data.market_api import MarketDataFetcher
import pandas as pd


class TestMarketDataFetcherContract:
    """Contract tests for MarketDataFetcher interface"""

    def test_fetch_with_fallback_returns_dict(self):
        """Test fetch_with_fallback returns dict with data and metadata"""
        fetcher = MarketDataFetcher()

        # This is a contract test, so we verify the structure
        result = fetcher.fetch_with_fallback(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        # Verify return type
        assert isinstance(result, dict), "fetch_with_fallback must return dict"

        # Verify required keys
        assert 'data' in result, "Result must contain 'data' key"
        assert 'metadata' in result, "Result must contain 'metadata' key"

        # Verify data is DataFrame
        assert isinstance(result['data'], pd.DataFrame), "data must be DataFrame"

        # Verify metadata is dict
        assert isinstance(result['metadata'], dict), "metadata must be dict"

    def test_metadata_includes_required_fields(self):
        """Test metadata includes api_source, retrieval_timestamp, data_freshness"""
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        metadata = result['metadata']

        # Verify required metadata fields
        assert 'api_source' in metadata, "metadata must include api_source"
        assert 'retrieval_timestamp' in metadata, "metadata must include retrieval_timestamp"
        assert 'data_freshness' in metadata, "metadata must include data_freshness"

        # Verify field types
        assert isinstance(metadata['api_source'], str), "api_source must be string"
        assert isinstance(metadata['retrieval_timestamp'], datetime), "retrieval_timestamp must be datetime"
        assert metadata['data_freshness'] in ['realtime', 'delayed', 'historical'], \
            "data_freshness must be one of: realtime, delayed, historical"

    def test_api_source_includes_version(self):
        """Test api_source includes version information"""
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        api_source = result['metadata']['api_source']

        # Should include version like "Efinance vlatest" or "AKShare v1.11.0"
        assert 'v' in api_source.lower() or 'latest' in api_source.lower(), \
            f"api_source should include version: got '{api_source}'"

    def test_data_freshness_realtime_condition(self):
        """Test data_freshness='realtime' when retrieval is fresh (<5s)"""
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        retrieval_time = result['metadata']['retrieval_timestamp']
        freshness = result['metadata']['data_freshness']

        # Calculate time since retrieval
        time_diff = (datetime.utcnow() - retrieval_time).total_seconds()

        # If just fetched (< 5s), should be realtime or delayed
        if time_diff < 5:
            assert freshness in ['realtime', 'delayed'], \
                f"Fresh data (<5s) should be 'realtime' or 'delayed', got '{freshness}'"

    def test_fetch_with_fallback_handles_symbol_formats(self):
        """Test fetcher handles both '600519.SH' and '600519' formats"""
        fetcher = MarketDataFetcher()

        # Both formats should work
        symbols = ["600519.SH", "600519"]

        for symbol in symbols:
            result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )

            assert result is not None, f"Should handle symbol format: {symbol}"
            assert len(result['data']) > 0, f"Should return data for: {symbol}"

    def test_data_contains_required_columns(self):
        """Test returned data contains OHLCV columns"""
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        data = result['data']

        # Verify OHLCV columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in data.columns, f"Data must include column: {col}"

    @pytest.mark.skip(reason="T008 not yet implemented - fallback to cache not ready")
    def test_fallback_chain_efinance_to_akshare_to_cache(self):
        """Test fallback chain: Efinance → AKShare → Cache

        This test is EXPECTED TO FAIL until T008 implementation.
        """
        # This test requires mocking API failures, which will be implemented in T008
        pytest.fail("T008 not implemented - cache fallback not ready")

    @pytest.mark.skip(reason="T008 not yet implemented - retry logic not enhanced")
    def test_retry_logic_exponential_backoff(self):
        """Test retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)

        This test is EXPECTED TO FAIL until T008 implementation.
        """
        # This test requires timing verification, which will be implemented in T008
        pytest.fail("T008 not implemented - enhanced retry not ready")

    def test_default_date_range(self):
        """Test fetcher uses default dates when not specified"""
        fetcher = MarketDataFetcher()

        # Call without dates
        result = fetcher.fetch_with_fallback(symbol="600519.SH")

        # Should still return data (using default 1-year range)
        assert result is not None
        assert len(result['data']) > 0
        assert 'metadata' in result

    def test_error_handling_invalid_symbol(self):
        """Test fetcher raises appropriate error for invalid symbol"""
        from investlib_data.market_api import NoDataAvailableError

        fetcher = MarketDataFetcher()

        # Invalid symbol should raise NoDataAvailableError after all fallbacks fail
        with pytest.raises(NoDataAvailableError, match="All data sources failed"):
            fetcher.fetch_with_fallback(
                symbol="INVALID_SYMBOL_999999",
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
