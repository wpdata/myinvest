"""Contract tests for CSV import CLI command.

These tests verify the import-csv command contract (interface, options, exit codes).
Tests written BEFORE implementation (TDD RED phase).
"""

import subprocess
import sys
import pytest
from pathlib import Path
import tempfile


class TestImportCSVContract:
    """Test import-csv CLI contract compliance."""

    def test_import_csv_help_command(self):
        """Test import-csv --help returns usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "import-csv", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "import-csv" in result.stdout.lower()
        assert "--file" in result.stdout.lower()

    def test_import_csv_requires_file_argument(self):
        """Test import-csv fails without --file argument."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "import-csv"],
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_import_csv_dry_run_previews_import(self):
        """Test import-csv --dry-run shows preview without importing."""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("symbol,purchase_date,purchase_price,quantity\n")
            f.write("600519.SH,2024-01-01,1500.00,100\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "investlib_data.cli", "import-csv",
                 "--file", temp_file, "--dry-run"],
                capture_output=True,
                text=True
            )

            # Should succeed
            assert result.returncode == 0
            # Should indicate dry run
            assert "dry" in result.stdout.lower() or "preview" in result.stdout.lower()

        finally:
            Path(temp_file).unlink()

    def test_import_csv_success_exit_code(self):
        """Test import-csv returns 0 on successful import (dry-run)."""
        # Create valid CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("symbol,purchase_date,purchase_price,quantity\n")
            f.write("600519.SH,2024-01-01,1500.00,100\n")
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "investlib_data.cli", "import-csv",
                 "--file", temp_file, "--dry-run"],
                capture_output=True
            )

            # Should succeed with exit code 0
            assert result.returncode == 0

        finally:
            Path(temp_file).unlink()
