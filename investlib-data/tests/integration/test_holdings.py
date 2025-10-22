"""Integration tests for the holdings calculation logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, InvestmentRecord, CurrentHolding, DataSource
from investlib_data.holdings import HoldingsCalculator
from datetime import date

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

class TestHoldingsCalculator:
    """Test the HoldingsCalculator class."""

    def test_calculate_holdings_from_records(self, db_session):
        """Test that holdings are correctly calculated from investment records."""
        # Add some investment records
        db_session.add_all([
            InvestmentRecord(symbol="AAPL", purchase_date=date(2023, 1, 1), purchase_price=150, quantity=10, purchase_amount=1500, data_source=DataSource.MANUAL_ENTRY, checksum="a"),
            InvestmentRecord(symbol="AAPL", purchase_date=date(2023, 2, 1), purchase_price=160, quantity=5, purchase_amount=800, data_source=DataSource.MANUAL_ENTRY, checksum="b"),
            InvestmentRecord(symbol="GOOG", purchase_date=date(2023, 3, 1), purchase_price=100, quantity=20, purchase_amount=2000, data_source=DataSource.MANUAL_ENTRY, checksum="c"),
        ])
        db_session.commit()

        calculator = HoldingsCalculator()
        calculator.calculate_holdings(db_session)

        holdings = db_session.query(CurrentHolding).all()
        assert len(holdings) == 2

        aapl_holding = db_session.query(CurrentHolding).filter_by(symbol="AAPL").one()
        assert aapl_holding.quantity == 15
        assert pytest.approx(aapl_holding.purchase_price) == ((150 * 10) + (160 * 5)) / 15

        goog_holding = db_session.query(CurrentHolding).filter_by(symbol="GOOG").one()
        assert goog_holding.quantity == 20
        assert goog_holding.purchase_price == 100

    def test_holdings_exclude_sold_positions(self, db_session):
        """Test that sold positions are excluded from current holdings."""
        db_session.add(InvestmentRecord(symbol="MSFT", purchase_date=date(2023, 1, 1), purchase_price=300, quantity=10, purchase_amount=3000, sale_date=date(2023, 6, 1), sale_price=350, data_source=DataSource.MANUAL_ENTRY, checksum="d"))
        db_session.commit()

        calculator = HoldingsCalculator()
        calculator.calculate_holdings(db_session)

        holdings = db_session.query(CurrentHolding).all()
        assert len(holdings) == 0
