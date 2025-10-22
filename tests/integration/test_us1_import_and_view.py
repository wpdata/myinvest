"""End-to-end test for User Story 1: Import and View Investment History."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, InvestmentRecord, CurrentHolding
from investlib_data.import_csv import CSVImporter
from investlib_data.holdings import HoldingsCalculator
from investapp.investapp.components.dashboard_backend import get_dashboard_data
import os

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

class TestUserStory1:
    """Test the full workflow of User Story 1."""

    def test_full_workflow(self, db_session):
        """Test the full workflow from CSV import to dashboard data generation."""
        # 1. Initialize database (done by fixture)

        # 2. Import sample CSV
        importer = CSVImporter()
        # Create a dummy csv file for the test
        csv_content = """symbol,purchase_date,purchase_price,quantity,sale_date,sale_price
600519.SH,2023-01-15,1500.00,100,2023-03-15,1600.00
000001.SZ,2023-02-20,12.50,1000,,
"""
        with open("test_us1.csv", "w") as f:
            f.write(csv_content)
        
        import_result = importer.save_to_database("test_us1.csv", db_session)
        os.remove("test_us1.csv")

        # 3. Verify records in database
        assert import_result["imported"] == 2
        records = db_session.query(InvestmentRecord).all()
        assert len(records) == 2

        # 4. Calculate holdings
        calculator = HoldingsCalculator()
        calculator.calculate_holdings(db_session)
        holdings = db_session.query(CurrentHolding).all()
        assert len(holdings) == 1
        assert holdings[0].symbol == "000001.SZ"

        # 5. Generate dashboard data
        # To get total_assets, we need to set a current_price for the holding
        holdings[0].current_price = 13.0
        db_session.commit()

        dashboard_data = get_dashboard_data(db_session)

        # 6. Verify dashboard data
        assert dashboard_data["total_assets"] == 1000 * 13.0
        assert len(dashboard_data["holdings"]) == 1
        # Profit/loss history should have entries for all transaction dates
        assert len(dashboard_data["profit_loss_history"]) >= 1

    def test_empty_database(self, db_session):
        """Test the workflow with an empty database."""
        dashboard_data = get_dashboard_data(db_session)
        assert dashboard_data["total_assets"] == 0
        assert len(dashboard_data["holdings"]) == 0
        assert len(dashboard_data["profit_loss_history"]) == 0
