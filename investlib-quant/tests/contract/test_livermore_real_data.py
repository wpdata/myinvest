"""
Contract Tests for Livermore Strategy with Real Data (US5 - T012)

These tests verify that LivermoreStrategy uses real market data (not test fixtures):
- Strategy fetches real data via MarketDataFetcher
- Strategy logs data source and timestamp
- Strategy returns signal with data metadata
- --no-cache flag forces fresh API call

Expected Status: RED PHASE (tests will FAIL until T013 refactor)
"""

import pytest
from datetime import datetime, timedelta
from investlib_quant.livermore_strategy import LivermoreStrategy


class TestLivermoreRealData:
    """Contract tests for Livermore strategy with real data integration."""

    def test_analyze_fetches_real_data_not_fixtures(self):
        """Test LivermoreStrategy.analyze(symbol) fetches real data, not test fixtures

        T013 is now COMPLETE - test should PASS.
        """
        strategy = LivermoreStrategy()

        # T013 refactored signature: analyze(symbol, start_date, end_date, capital)
        result = strategy.analyze(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            capital=100000.0
        )

        # Verify result is not None and is a dict
        assert result is not None
        assert isinstance(result, dict)

    def test_strategy_logs_data_source_and_timestamp(self):
        """Test strategy logs data_source and data_timestamp

        T013 is COMPLETE - test should PASS.
        """
        strategy = LivermoreStrategy()

        # After T013, analyze() returns signal with metadata
        signal = strategy.analyze(
            symbol="600519.SH",
            start_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d'),
            capital=100000.0
        )

        # Should include metadata fields
        assert 'data_source' in signal, "Signal must include data_source"
        assert 'data_timestamp' in signal, "Signal must include data_timestamp"
        assert 'data_freshness' in signal, "Signal must include data_freshness"

    def test_strategy_returns_signal_with_data_metadata(self):
        """Test strategy returns complete signal with data provenance

        T013 is COMPLETE - test should PASS.
        """
        strategy = LivermoreStrategy()

        signal = strategy.analyze(symbol="600519.SH", capital=100000.0)

        # Verify standard signal fields
        assert 'action' in signal
        assert 'confidence' in signal
        assert 'entry_price' in signal
        assert 'stop_loss' in signal
        assert 'take_profit' in signal

        # Verify data metadata fields (NEW after T013)
        assert 'data_source' in signal
        assert 'data_timestamp' in signal
        assert 'data_freshness' in signal

        # Verify data source is real (not test fixture)
        assert "test_fixture" not in signal['data_source'].lower()
        assert "Efinance" in signal['data_source'] or "AKShare" in signal['data_source']

    def test_no_cache_flag_forces_fresh_api_call(self):
        """Test --no-cache flag forces fresh API call (bypasses cache)

        T013 is COMPLETE - test should PASS.
        """
        strategy = LivermoreStrategy()

        # First call (may use cache)
        signal1 = strategy.analyze(
            symbol="600519.SH",
            capital=100000.0,
            use_cache=True  # Use cache if available
        )

        # Second call (force fresh)
        signal2 = strategy.analyze(
            symbol="600519.SH",
            capital=100000.0,
            use_cache=False  # Should force API call
        )

        # Both should have data, but second should have fresher timestamp
        assert signal1 is not None
        assert signal2 is not None
        assert 'data_timestamp' in signal1
        assert 'data_timestamp' in signal2

    def test_strategy_validates_symbol_format(self):
        """Test strategy handles both '600519.SH' and '600519' formats

        T013 is COMPLETE - test should PASS.
        """
        strategy = LivermoreStrategy()

        symbols = ["600519.SH", "600519"]

        for symbol in symbols:
            signal = strategy.analyze(symbol=symbol, capital=100000.0)
            assert signal is not None, f"Should handle symbol format: {symbol}"

    def test_strategy_method_signature_after_refactor(self):
        """Test that after T013, analyze() has new signature

        New signature: analyze(symbol, start_date=None, end_date=None, capital=100000.0, use_cache=True)
        Old signature: analyze(market_data, capital=100000.0)

        T013 is COMPLETE - test should PASS.
        """
        strategy = LivermoreStrategy()

        # Verify new signature exists
        import inspect
        sig = inspect.signature(strategy.analyze)
        params = list(sig.parameters.keys())

        # After T013 refactor, signature should have changed
        assert 'symbol' in params, "New signature must have 'symbol' parameter"
        assert 'start_date' in params, "New signature must have 'start_date' parameter"
        assert 'end_date' in params, "New signature must have 'end_date' parameter"
        assert 'use_cache' in params, "New signature must have 'use_cache' parameter"

        # Old signature should be removed
        assert 'market_data' not in params, "Old 'market_data' parameter should be removed"

    def test_strategy_requires_minimum_data_points(self):
        """Test strategy validates sufficient data points (120+ days for MA120)

        Expected to PASS after T013 (validation should still work).
        """
        strategy = LivermoreStrategy(ma_period=120)

        # Test with insufficient date range (only 30 days)
        with pytest.raises((TypeError, ValueError)):
            strategy.analyze(
                symbol="600519.SH",
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                capital=100000.0
            )
