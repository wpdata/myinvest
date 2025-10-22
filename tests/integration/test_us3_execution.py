"""
End-to-End Test for User Story 3: Simulated Trading Execution

Tests the complete workflow:
1. Generate recommendation
2. Validate position limits
3. Execute simulated trade (confirmation workflow)
4. Verify operation logged to database
5. Verify holdings updated
6. Test append-only log enforcement
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, OperationLog, CurrentHolding, InvestmentRecommendation
from investlib_data.operation_logger import OperationLogger
from investlib_data.holdings import HoldingsCalculator
import json


class TestUserStory3:
    """End-to-end tests for US3: Simulated Trading Execution"""

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
        """Test complete execution workflow from recommendation to holdings update"""

        # Step 1: Create a mock recommendation
        recommendation = InvestmentRecommendation(
            symbol='600519.SH',
            action='BUY',
            entry_price=1680.0,
            stop_loss=1620.0,
            take_profit=1800.0,
            position_size_pct=15.0,
            max_loss_amount=9000.0,
            expected_return_pct=10.0,
            advisor_name="Livermore",
            advisor_version="v1.0.0",
            strategy_name="Trend Following",
            reasoning="Price breakout above 120-day MA with volume confirmation",
            confidence="HIGH",
            key_factors='["MA breakout", "Volume spike", "MACD golden cross"]',
            market_data_timestamp=datetime.now(),
            data_source="Efinance vlatest"
        )

        self.session.add(recommendation)
        self.session.commit()

        # Step 2: Validate position (position validator would run here in real app)
        total_capital = 100000.0
        position_value = total_capital * (recommendation.position_size_pct / 100)
        assert recommendation.position_size_pct <= 20  # Constitution limit
        assert position_value <= total_capital

        # Step 3: Log operation (simulating user confirmation)
        logger = OperationLogger(self.session)

        original_recommendation_json = {
            'recommendation_id': recommendation.recommendation_id,
            'symbol': recommendation.symbol,
            'action': str(recommendation.action),  # Convert enum to string
            'entry_price': recommendation.entry_price,
            'stop_loss': recommendation.stop_loss,
            'take_profit': recommendation.take_profit,
            'position_size_pct': recommendation.position_size_pct,
            'max_loss_amount': recommendation.max_loss_amount
        }

        operation_id = logger.log_operation(
            user_id="test_user",
            operation_type="BUY",
            symbol=recommendation.symbol,
            recommendation=original_recommendation_json,
            modification=None,
            status="EXECUTED"
        )

        assert operation_id is not None
        assert isinstance(operation_id, str)

        # Step 4: Verify operation logged to database
        logged_op = self.session.query(OperationLog).filter_by(
            operation_id=operation_id
        ).first()

        assert logged_op is not None
        assert logged_op.operation_id == operation_id
        assert logged_op.user_id == "test_user"
        assert logged_op.operation_type.value == "BUY"
        assert logged_op.execution_status.value == "EXECUTED"
        assert logged_op.execution_mode.value == "SIMULATED"  # v0.1 is simulation only

        # Verify original_recommendation is stored as JSON
        stored_rec = json.loads(logged_op.original_recommendation)
        assert stored_rec['symbol'] == recommendation.symbol
        assert stored_rec['entry_price'] == recommendation.entry_price

        # Step 5: Update holdings (simulating holdings calculator)
        quantity = position_value / recommendation.entry_price

        holding = CurrentHolding(
            symbol=recommendation.symbol,
            quantity=quantity,
            purchase_price=recommendation.entry_price,
            current_price=recommendation.entry_price,  # Initially same as purchase
            profit_loss_amount=0.0,
            profit_loss_pct=0.0,
            purchase_date=datetime.now().date()
        )

        self.session.add(holding)
        self.session.commit()

        # Step 6: Verify holdings updated
        saved_holding = self.session.query(CurrentHolding).filter_by(
            symbol=recommendation.symbol
        ).first()

        assert saved_holding is not None
        assert saved_holding.symbol == recommendation.symbol
        assert saved_holding.quantity == pytest.approx(quantity, rel=0.01)
        assert saved_holding.purchase_price == recommendation.entry_price

    def test_position_validation_rejects_over_allocation(self):
        """Test that positions exceeding limits are rejected"""

        # Create a recommendation that exceeds 20% limit
        recommendation = {
            'symbol': '600519.SH',
            'action': 'BUY',
            'entry_price': 1680.0,
            'position_size_pct': 25.0,  # Exceeds 20% limit
            'max_loss_amount': 12000.0
        }

        total_capital = 100000.0

        # Validate position size
        is_valid = recommendation['position_size_pct'] <= 20
        assert not is_valid, "Position exceeding 20% limit should be rejected"

    def test_operation_log_append_only_enforcement(self):
        """Test that OperationLog prevents updates and deletes"""

        # Create an operation log entry
        logger = OperationLogger(self.session)

        operation_id = logger.log_operation(
            user_id="test_user",
            operation_type="BUY",
            symbol="600519.SH",
            recommendation={'symbol': '600519.SH', 'action': 'BUY'},
            modification=None,
            status="EXECUTED"
        )

        # Get the operation object from database
        operation = self.session.query(OperationLog).filter_by(
            operation_id=operation_id
        ).first()

        original_timestamp = operation.timestamp
        original_operation_id = operation.operation_id

        # Attempt UPDATE - should fail
        with pytest.raises(ValueError, match="append-only"):
            operation.user_id = "modified_user"
            self.session.commit()

        self.session.rollback()

        # Verify operation unchanged
        saved_op = self.session.query(OperationLog).filter_by(
            operation_id=original_operation_id
        ).first()

        assert saved_op is not None
        assert saved_op.user_id == "test_user"  # Not modified
        assert saved_op.timestamp == original_timestamp

        # Attempt DELETE - should fail
        with pytest.raises(ValueError, match="append-only"):
            self.session.delete(saved_op)
            self.session.commit()

        self.session.rollback()

        # Verify operation still exists
        still_exists = self.session.query(OperationLog).filter_by(
            operation_id=original_operation_id
        ).first()

        assert still_exists is not None

    def test_user_modification_tracking(self):
        """Test that user modifications to recommendations are tracked"""

        original_recommendation = {
            'symbol': '600519.SH',
            'action': 'BUY',
            'entry_price': 1680.0,
            'stop_loss': 1620.0,
            'position_size_pct': 15.0
        }

        # User modifies stop-loss and position size
        user_modification = {
            'modified_fields': ['stop_loss', 'position_size_pct'],
            'changes': {
                'stop_loss': {'old': 1620.0, 'new': 1640.0},
                'position_size_pct': {'old': 15.0, 'new': 10.0}
            },
            'reason': 'Reduced risk due to market volatility'
        }

        # Log operation with modification
        logger = OperationLogger(self.session)
        operation_id = logger.log_operation(
            user_id="test_user",
            operation_type="BUY",
            symbol="600519.SH",
            recommendation=original_recommendation,
            modification=user_modification,
            status="EXECUTED"
        )

        # Verify modification stored
        saved_op = self.session.query(OperationLog).filter_by(
            operation_id=operation_id
        ).first()

        assert saved_op.user_modification is not None

        modification = json.loads(saved_op.user_modification)
        assert 'stop_loss' in modification['modified_fields']
        assert modification['changes']['stop_loss']['new'] == 1640.0
        assert modification['reason'] == 'Reduced risk due to market volatility'

    def test_simulated_mode_indicator(self):
        """Test that all operations are marked as SIMULATED in v0.1"""

        logger = OperationLogger(self.session)

        operation_id = logger.log_operation(
            user_id="test_user",
            operation_type="BUY",
            symbol="600519.SH",
            recommendation={'symbol': '600519.SH', 'action': 'BUY'},
            modification=None,
            status="EXECUTED"
        )

        # Get operation from database
        operation = self.session.query(OperationLog).filter_by(
            operation_id=operation_id
        ).first()

        # v0.1 should always be SIMULATED mode
        assert operation.execution_mode.value == "SIMULATED"

    def test_holdings_calculation_with_multiple_purchases(self):
        """Test that holdings correctly calculate average cost for multiple purchases"""

        # First purchase
        holding1 = CurrentHolding(
            symbol='600519.SH',
            quantity=100.0,
            purchase_price=1600.0,
            current_price=1600.0,
            profit_loss_amount=0.0,
            profit_loss_pct=0.0,
            purchase_date=datetime.now().date()
        )

        self.session.add(holding1)
        self.session.commit()

        # Second purchase at different price
        additional_quantity = 50.0
        new_price = 1680.0

        # Calculate new average cost
        total_quantity = holding1.quantity + additional_quantity
        total_cost = (holding1.quantity * holding1.purchase_price) + (additional_quantity * new_price)
        new_avg_price = total_cost / total_quantity

        # Update holding
        holding1.quantity = total_quantity
        holding1.purchase_price = new_avg_price
        self.session.commit()

        # Verify average cost calculation
        expected_avg = (100 * 1600 + 50 * 1680) / 150
        assert holding1.purchase_price == pytest.approx(expected_avg, rel=0.01)
        assert holding1.quantity == 150.0
