"""Contract tests for investlib-data CLI interface.

These tests verify the CLI contract (commands, options, exit codes)
WITHOUT testing implementation details.
"""

import subprocess
import sys
import pytest


class TestCLIContract:
    """Test investlib-data CLI contract compliance."""

    def test_cli_help_command(self):
        """Test --help returns usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "investlib-data" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_init_db_help_command(self):
        """Test init-db --help shows command-specific help."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "init-db", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "init-db" in result.stdout.lower()

    def test_init_db_dry_run(self):
        """Test init-db --dry-run shows preview without creating database."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "init-db", "--dry-run"],
            capture_output=True,
            text=True
        )

        # Should succeed with preview message
        assert result.returncode == 0
        assert "dry" in result.stdout.lower() or "preview" in result.stdout.lower()

    def test_cli_success_exit_code(self):
        """Test CLI returns exit code 0 on success."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "--help"],
            capture_output=True
        )

        assert result.returncode == 0

    def test_cli_error_exit_code_on_invalid_command(self):
        """Test CLI returns non-zero exit code on invalid command."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "nonexistent-command"],
            capture_output=True
        )

        # Should fail with exit code 2 (Click's convention for usage errors)
        assert result.returncode != 0


class TestFetchMarketCLI:
    """Test fetch-market CLI contract (will be implemented later)."""

    @pytest.mark.skip(reason="fetch-market command not implemented in Foundation phase")
    def test_fetch_market_help(self):
        """Test fetch-market --help shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "fetch-market", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "fetch-market" in result.stdout.lower()


class TestCacheStatsCLI:
    """Test cache-stats CLI contract."""

    @pytest.mark.skip(reason="cache-stats command implementation pending")
    def test_cache_stats_command(self):
        """Test cache-stats returns statistics."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_data.cli", "cache-stats"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
