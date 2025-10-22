"""
End-to-End Test for User Story 2: Investment Recommendations

Tests the complete workflow:
1. Fetch market data
2. Generate signal with investlib-quant
3. Generate recommendation with investlib-advisors
4. Verify mandatory fields and validation
5. Verify database persistence
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, InvestmentRecommendation, MarketDataPoint
from investlib_data.market_api import MarketDataFetcher
from investlib_quant.signal_generator import SignalGenerator
from investlib_advisors.livermore_advisor import LivermoreAdvisor


class TestUserStory2:
    """End-to-end tests for US2: Investment Recommendations"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup in-memory database for each test"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        yield
        self.session.close()

    def test_full_workflow(self):
        """Test complete recommendation generation workflow"""
        # Step 1: Fetch market data
        fetcher = MarketDataFetcher()
        symbol = "600519.SH"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        try:
            market_data_result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data = market_data_result['data']
        except Exception as e:
            pytest.skip(f"Market data API unavailable: {e}")

        assert market_data is not None
        assert len(market_data) > 0

        # Step 2: Generate signal with investlib-quant
        signal_generator = SignalGenerator()
        capital = 100000.0  # Test capital

        signal = signal_generator.generate_trading_signal(
            symbol=symbol,
            market_data=market_data,
            capital=capital
        )

        # Verify signal structure
        assert signal is not None
        assert 'action' in signal
        assert 'entry_price' in signal
        assert 'stop_loss' in signal
        assert 'take_profit' in signal
        assert 'position_size_pct' in signal or 'position_value' in signal
        assert 'max_loss' in signal

        # Step 3: Generate recommendation with investlib-advisors
        advisor = LivermoreAdvisor()
        recommendation_dict = advisor.generate_recommendation(
            signal=signal,
            capital=capital
        )

        # Step 4: Verify all mandatory fields present in dict
        assert recommendation_dict is not None
        assert recommendation_dict['symbol'] == symbol
        assert recommendation_dict['action'] in ['BUY', 'SELL', 'HOLD']
        assert recommendation_dict['entry_price'] > 0
        assert recommendation_dict['stop_loss'] is not None
        assert recommendation_dict['stop_loss'] > 0
        assert recommendation_dict['take_profit'] > 0
        assert recommendation_dict['position_size_pct'] > 0
        assert recommendation_dict['position_size_pct'] <= 20  # Constitution limit
        assert recommendation_dict['max_loss'] > 0

        # Verify advisor metadata
        assert recommendation_dict['advisor_name'] == "Livermore"
        assert recommendation_dict['advisor_version'].startswith("v")
        assert recommendation_dict['strategy_name'] == "Trend Following"

        # Verify explainability fields
        assert recommendation_dict['reasoning'] is not None
        assert len(recommendation_dict['reasoning']) > 0
        assert recommendation_dict['confidence'] in ['HIGH', 'MEDIUM', 'LOW']
        assert recommendation_dict['key_factors'] is not None

        # Step 5: Verify stop-loss validation
        if recommendation_dict['action'] == 'BUY':
            assert recommendation_dict['stop_loss'] < recommendation_dict['entry_price'], \
                "BUY stop-loss must be below entry price"
        elif recommendation_dict['action'] == 'SELL':
            assert recommendation_dict['stop_loss'] > recommendation_dict['entry_price'], \
                "SELL stop-loss must be above entry price"

        # Step 6: Create model object and save to database
        recommendation = InvestmentRecommendation(
            symbol=recommendation_dict['symbol'],
            action=recommendation_dict['action'],
            entry_price=recommendation_dict['entry_price'],
            stop_loss=recommendation_dict['stop_loss'],
            take_profit=recommendation_dict['take_profit'],
            position_size_pct=recommendation_dict['position_size_pct'],
            max_loss_amount=recommendation_dict['max_loss'],
            expected_return_pct=recommendation_dict.get('expected_return_pct', 0.0),
            advisor_name=recommendation_dict['advisor_name'],
            advisor_version=recommendation_dict['advisor_version'],
            strategy_name=recommendation_dict['strategy_name'],
            reasoning=recommendation_dict['reasoning'],
            confidence=recommendation_dict['confidence'],
            key_factors=str(recommendation_dict['key_factors']),
            market_data_timestamp=datetime.now(),
            data_source=market_data_result['metadata']['api_source']
        )

        self.session.add(recommendation)
        self.session.commit()

        # Query back from database
        saved_rec = self.session.query(InvestmentRecommendation).filter_by(
            symbol=symbol
        ).first()

        assert saved_rec is not None
        assert saved_rec.recommendation_id == recommendation.recommendation_id
        assert saved_rec.stop_loss == recommendation.stop_loss

    def test_recommendation_includes_mandatory_stop_loss(self):
        """Test that all generated recommendations include mandatory stop-loss"""
        # This test validates Constitution Principle VIII: Investment Safety
        # All recommendations MUST have stop-loss field populated

        fetcher = MarketDataFetcher()
        symbol = "600519.SH"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        try:
            market_data_result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data = market_data_result['data']
        except Exception:
            pytest.skip("Market data API unavailable")

        signal_generator = SignalGenerator()
        signal = signal_generator.generate_trading_signal(
            symbol=symbol,
            market_data=market_data,
            capital=100000.0
        )

        # Verify signal includes stop_loss
        assert 'stop_loss' in signal
        assert signal['stop_loss'] is not None
        assert signal['stop_loss'] > 0

        advisor = LivermoreAdvisor()
        recommendation = advisor.generate_recommendation(
            signal=signal,
            capital=100000.0
        )

        # Verify recommendation includes stop_loss
        assert recommendation['stop_loss'] is not None
        assert recommendation['stop_loss'] > 0

    def test_data_provenance_recorded(self):
        """Test that data provenance fields are properly recorded"""
        fetcher = MarketDataFetcher()
        symbol = "600519.SH"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        try:
            market_data_result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data = market_data_result['data']
        except Exception:
            pytest.skip("Market data API unavailable")

        signal_generator = SignalGenerator()
        signal = signal_generator.generate_trading_signal(
            symbol=symbol,
            market_data=market_data,
            capital=100000.0
        )

        advisor = LivermoreAdvisor()
        recommendation = advisor.generate_recommendation(
            signal=signal,
            capital=100000.0
        )

        # Verify data provenance fields in signal and metadata
        assert market_data_result['metadata']['retrieval_timestamp'] is not None
        assert market_data_result['metadata']['api_source'] is not None
        assert "Efinance" in market_data_result['metadata']['api_source'] or "AKShare" in market_data_result['metadata']['api_source']
        assert recommendation['generated_at'] is not None

    def test_confidence_calculation(self):
        """Test that confidence levels are assigned correctly"""
        fetcher = MarketDataFetcher()
        symbol = "600519.SH"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        try:
            market_data_result = fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data = market_data_result['data']
        except Exception:
            pytest.skip("Market data API unavailable")

        signal_generator = SignalGenerator()
        signal = signal_generator.generate_trading_signal(
            symbol=symbol,
            market_data=market_data,
            capital=100000.0
        )

        advisor = LivermoreAdvisor()
        recommendation = advisor.generate_recommendation(
            signal=signal,
            capital=100000.0
        )

        # Verify confidence is one of the valid values
        assert recommendation['confidence'] in ['HIGH', 'MEDIUM', 'LOW']

        # Confidence should correlate with signal strength
        if signal.get('confidence') == 'HIGH':
            assert recommendation['confidence'] in ['HIGH', 'MEDIUM']
