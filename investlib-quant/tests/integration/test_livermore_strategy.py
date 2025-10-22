"""Integration tests for Livermore strategy.

These tests verify the Livermore trend-following strategy with real calculations.
Tests written BEFORE implementation (TDD RED phase).
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


# This will fail until implementation exists
try:
    from investlib_quant.livermore_strategy import LivermoreStrategy
    STRATEGY_EXISTS = True
except ImportError:
    STRATEGY_EXISTS = False


@pytest.fixture
def bullish_breakout_data():
    """Create market data showing bullish breakout pattern."""
    # Generate 200 days of data with upward breakout
    dates = [(datetime(2024, 1, 1) + timedelta(days=i)) for i in range(200)]

    # Prices consolidating around 1500, then breaking out
    base_prices = [1500 + (i * 0.5 if i < 150 else (i - 150) * 5) for i in range(200)]

    data = pd.DataFrame({
        'timestamp': dates,
        'open': [p * 0.99 for p in base_prices],
        'high': [p * 1.02 for p in base_prices],
        'low': [p * 0.98 for p in base_prices],
        'close': base_prices,
        'volume': [1000000 + (i * 10000 if i >= 150 else 0) for i in range(200)]
    })

    return data


@pytest.fixture
def bearish_breakdown_data():
    """Create market data showing bearish breakdown pattern."""
    dates = [(datetime(2024, 1, 1) + timedelta(days=i)) for i in range(200)]

    # Prices consolidating, then breaking down
    base_prices = [1500 - (i * 0.5 if i < 150 else (i - 150) * 5) for i in range(200)]

    data = pd.DataFrame({
        'timestamp': dates,
        'open': [p * 1.01 for p in base_prices],
        'high': [p * 1.02 for p in base_prices],
        'low': [p * 0.98 for p in base_prices],
        'close': base_prices,
        'volume': [1000000 + (i * 10000 if i >= 150 else 0) for i in range(200)]
    })

    return data


@pytest.fixture
def sideways_market_data():
    """Create market data showing sideways consolidation."""
    dates = [(datetime(2024, 1, 1) + timedelta(days=i)) for i in range(200)]

    # Prices oscillating around 1500
    import math
    base_prices = [1500 + 50 * math.sin(i * 0.1) for i in range(200)]

    data = pd.DataFrame({
        'timestamp': dates,
        'open': [p * 0.99 for p in base_prices],
        'high': [p * 1.02 for p in base_prices],
        'low': [p * 0.98 for p in base_prices],
        'close': base_prices,
        'volume': [1000000] * 200
    })

    return data


@pytest.mark.skipif(not STRATEGY_EXISTS, reason="LivermoreStrategy not yet implemented")
class TestLivermoreStrategy:
    """Test Livermore strategy signal generation."""

    def test_bullish_breakout_generates_buy_signal(self, bullish_breakout_data):
        """Test strategy generates BUY signal for bullish breakout."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bullish_breakout_data)

        assert signal is not None
        assert signal['action'] in ['BUY', 'STRONG_BUY']
        assert signal['confidence'] in ['HIGH', 'MEDIUM', 'LOW']
        assert 'entry_price' in signal
        assert 'stop_loss' in signal
        assert 'take_profit' in signal
        assert 'position_size_pct' in signal

        # Verify stop-loss logic for BUY
        assert signal['stop_loss'] < signal['entry_price']

    def test_bearish_breakdown_generates_sell_signal(self, bearish_breakdown_data):
        """Test strategy generates SELL signal for bearish breakdown."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bearish_breakdown_data)

        assert signal is not None
        assert signal['action'] in ['SELL', 'STRONG_SELL']

        # Verify stop-loss logic for SELL
        if signal['action'] in ['SELL', 'STRONG_SELL']:
            assert signal['stop_loss'] > signal['entry_price']

    def test_sideways_market_generates_hold_signal(self, sideways_market_data):
        """Test strategy generates HOLD or low confidence signal for sideways market."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(sideways_market_data)

        assert signal is not None
        # Sideways market should generate HOLD or low confidence signal
        # Note: Due to oscillating pattern, it may trigger weak BUY/SELL signals
        assert signal['action'] in ['HOLD', 'BUY', 'SELL']
        # Confidence should not be HIGH for sideways market
        assert signal['confidence'] in ['MEDIUM', 'LOW']

    def test_all_signals_include_mandatory_fields(self, bullish_breakout_data):
        """Test all signals include mandatory safety fields."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bullish_breakout_data)

        # Mandatory fields per Constitution Principle VIII
        required_fields = [
            'action',
            'entry_price',
            'stop_loss',
            'take_profit',
            'position_size_pct',
            'confidence'
        ]

        for field in required_fields:
            assert field in signal, f"Missing mandatory field: {field}"
            assert signal[field] is not None, f"Field {field} is None"

        # Verify stop_loss is present (Constitution requirement)
        assert signal['stop_loss'] > 0

    def test_stop_loss_validation_for_buy(self, bullish_breakout_data):
        """Test stop-loss validation: BUY signals have stop < entry."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bullish_breakout_data)

        if signal['action'] in ['BUY', 'STRONG_BUY']:
            assert signal['stop_loss'] < signal['entry_price'], \
                "BUY signal: stop_loss must be below entry_price"

    def test_stop_loss_validation_for_sell(self, bearish_breakdown_data):
        """Test stop-loss validation: SELL signals have stop > entry."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bearish_breakdown_data)

        if signal['action'] in ['SELL', 'STRONG_SELL']:
            assert signal['stop_loss'] > signal['entry_price'], \
                "SELL signal: stop_loss must be above entry_price"

    def test_position_size_within_limits(self, bullish_breakout_data):
        """Test position sizing respects 0-20% limits."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bullish_breakout_data)

        assert 0 <= signal['position_size_pct'] <= 20, \
            "Position size must be between 0% and 20%"

    def test_risk_reward_ratio_minimum(self, bullish_breakout_data):
        """Test risk-reward ratio meets minimum requirement (1:3)."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bullish_breakout_data)

        if signal['action'] in ['BUY', 'STRONG_BUY']:
            risk = signal['entry_price'] - signal['stop_loss']
            reward = signal['take_profit'] - signal['entry_price']
            ratio = reward / risk if risk > 0 else 0

            assert ratio >= 3.0, f"Risk-reward ratio {ratio} is below minimum 1:3"

    def test_key_factors_included(self, bullish_breakout_data):
        """Test signal includes key_factors for explainability."""
        strategy = LivermoreStrategy()
        signal = strategy.analyze(bullish_breakout_data)

        assert 'key_factors' in signal
        assert isinstance(signal['key_factors'], list)
        assert len(signal['key_factors']) > 0

        # Expected factors for Livermore strategy
        factors_text = ' '.join(signal['key_factors']).lower()
        # Should mention at least one indicator
        assert any(keyword in factors_text for keyword in
                   ['ma', 'moving average', 'volume', 'macd', 'breakout'])
