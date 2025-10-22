"""Integration tests for database initialization and ORM models."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, OperationLog, InvestmentRecord
import uuid

@pytest.fixture(scope="module")
def engine():
    """Create an in-memory SQLite database engine for tests."""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="module")
def tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
    return Base.metadata.tables

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test function."""
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

class TestDatabaseInitialization:
    """Test database schema creation."""

    def test_all_tables_created(self, tables):
        """Verify that all 6 models are created as tables."""
        table_names = tables.keys()
        assert len(table_names) == 6
        assert "investment_records" in table_names
        assert "market_data" in table_names
        assert "investment_recommendations" in table_names
        assert "operation_log" in table_names
        assert "account_balances" in table_names
        assert "current_holdings" in table_names

    def test_investment_record_columns(self, tables):
        """Verify the columns of the investment_records table."""
        inspector = inspect(tables['investment_records'])
        columns = [col.name for col in inspector.columns]
        assert "record_id" in columns
        assert "symbol" in columns
        assert "purchase_price" in columns
        assert "quantity" in columns
        assert "checksum" in columns

class TestOperationLogAppendOnly:
    """Test the append-only enforcement for the OperationLog model."""

    def test_create_operation_log_succeeds(self, db_session):
        """Test that creating a new OperationLog entry works."""
        log_entry = OperationLog(
            operation_id=str(uuid.uuid4()),
            user_id="test_user",
            operation_type="BUY",
            symbol="600519.SH",
            original_recommendation='{"action": "BUY"}',
            execution_status="EXECUTED"
        )
        db_session.add(log_entry)
        db_session.commit()
        
        retrieved = db_session.query(OperationLog).first()
        assert retrieved is not None
        assert retrieved.user_id == "test_user"

    def test_update_operation_log_fails(self, db_session):
        """Test that updating an OperationLog entry raises a ValueError."""
        log_entry = OperationLog(
            operation_id=str(uuid.uuid4()),
            user_id="test_user",
            operation_type="BUY",
            symbol="600519.SH",
            original_recommendation='{"action": "BUY"}',
            execution_status="EXECUTED"
        )
        db_session.add(log_entry)
        db_session.commit()

        retrieved = db_session.query(OperationLog).first()
        retrieved.user_id = "new_user"
        
        with pytest.raises(ValueError, match="OperationLog is append-only, updates not allowed"):
            db_session.commit()

    def test_delete_operation_log_fails(self, db_session):
        """Test that deleting an OperationLog entry raises a ValueError."""
        log_entry = OperationLog(
            operation_id=str(uuid.uuid4()),
            user_id="test_user",
            operation_type="BUY",
            symbol="600519.SH",
            original_recommendation='{"action": "BUY"}',
            execution_status="EXECUTED"
        )
        db_session.add(log_entry)
        db_session.commit()

        retrieved = db_session.query(OperationLog).first()
        db_session.delete(retrieved)

        with pytest.raises(ValueError, match="OperationLog is append-only, deletes not allowed"):
            db_session.commit()
