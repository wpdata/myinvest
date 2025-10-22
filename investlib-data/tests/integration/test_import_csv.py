"""Integration tests for the CSV import logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base, InvestmentRecord
from investlib_data.import_csv import CSVImporter
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

class TestCSVImporter:
    """Test the CSVImporter class."""

    def test_import_valid_csv(self, db_session):
        """Test importing a valid CSV file inserts all records."""
        importer = CSVImporter()
        file_path = "investlib-data/tests/valid.csv"
        result = importer.save_to_database(file_path, db_session)

        assert result["imported"] == 2
        assert result["rejected"] == 0
        assert len(db_session.query(InvestmentRecord).all()) == 2

    def test_import_invalid_csv(self, db_session):
        """Test importing an invalid CSV file rejects all records."""
        importer = CSVImporter()
        file_path = "investlib-data/tests/invalid.csv"
        result = importer.save_to_database(file_path, db_session)

        assert result["imported"] == 0
        assert result["rejected"] == 2
        assert len(db_session.query(InvestmentRecord).all()) == 0
        assert len(result["errors"]) == 2

    def test_import_mixed_csv(self, db_session):
        """Test importing a mixed CSV file imports valid and rejects invalid records."""
        importer = CSVImporter()
        file_path = "investlib-data/tests/mixed.csv"
        result = importer.save_to_database(file_path, db_session)

        assert result["imported"] == 1
        assert result["rejected"] == 1
        assert len(db_session.query(InvestmentRecord).all()) == 1
        assert len(result["errors"]) == 1

    def test_checksum_calculation(self, db_session):
        """Test that the checksum is calculated and stored correctly."""
        importer = CSVImporter()
        file_path = "investlib-data/tests/valid.csv"
        importer.save_to_database(file_path, db_session)

        record = db_session.query(InvestmentRecord).first()
        assert record.checksum is not None
        # Expected checksum for the first record in valid.csv
        # SHA256("600519.SH2023-01-151500.0100")
        expected_checksum = "ce5faa57bbe64fb5639b5aca6ef3036683a773ba37dec313dff5fc54be0435d5"
        assert record.checksum == expected_checksum
