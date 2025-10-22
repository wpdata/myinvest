"""Integration tests for the dashboard backend logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, InvestmentRecord, CurrentHolding, DataSource
from investapp.investapp.components.dashboard_backend import get_dashboard_data
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

class TestDashboardBackend:
    """Test the dashboard backend functions."""

    def test_get_dashboard_data_empty_db(self, db_session):
        """Test with an empty database."""
        data = get_dashboard_data(db_session)
        assert data["total_assets"] == 0
        assert len(data["holdings"]) == 0
        assert len(data["profit_loss_history"]) == 0

    def test_get_dashboard_data_with_sample_data(self, db_session):
        """Test with sample investment records."""
        # Add holdings
        db_session.add_all([
            CurrentHolding(symbol="AAPL", quantity=10, purchase_price=150, current_price=170, purchase_date=date(2023,1,1), profit_loss_amount=200, profit_loss_pct=13.33),
            CurrentHolding(symbol="GOOG", quantity=5, purchase_price=100, current_price=110, purchase_date=date(2023,2,1), profit_loss_amount=50, profit_loss_pct=10.0),
        ])
        db_session.commit()

        data = get_dashboard_data(db_session)

        assert data["total_assets"] == (10 * 170) + (5 * 110)
        assert len(data["holdings"]) == 2
        # Profit loss history is not tested in detail here as it requires more complex data
        assert "profit_loss_history" in data
