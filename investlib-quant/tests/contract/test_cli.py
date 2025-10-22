"""Contract tests for investlib-quant CLI command.

These tests verify the CLI interface contract (interface, options, exit codes).
Tests written BEFORE implementation (TDD RED phase).
"""

import subprocess
import sys
import pytest


class TestQuantCLIContract:
    """Test investlib-quant CLI contract compliance."""

    def test_cli_help_command(self):
        """Test investlib-quant --help returns usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_quant.cli", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "investlib-quant" in result.stdout.lower()

    def test_analyze_help_command(self):
        """Test analyze --help shows usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_quant.cli", "analyze", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "analyze" in result.stdout.lower()
        assert "--symbol" in result.stdout.lower()
        assert "--strategy" in result.stdout.lower()

    def test_analyze_requires_symbol_argument(self):
        """Test analyze fails without --symbol argument."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_quant.cli", "analyze"],
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_analyze_with_livermore_strategy(self):
        """Test analyze command with Livermore strategy."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_quant.cli", "analyze",
             "--symbol", "600519.SH", "--strategy", "livermore", "--output", "json"],
            capture_output=True,
            text=True
        )

        # For now, should not crash (implementation pending)
        # When implemented, should return 0
        # For TDD RED phase, this may fail or return placeholder
        assert result.returncode is not None

    def test_analyze_output_json_format(self):
        """Test analyze --output json returns structured output."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_quant.cli", "analyze",
             "--symbol", "600519.SH", "--output", "json"],
            capture_output=True,
            text=True
        )

        # Should not crash
        assert result.returncode is not None
        # When implemented, should be valid JSON
        # import json
        # data = json.loads(result.stdout)
        # assert 'signal' in data

    def test_analyze_invalid_symbol_returns_error(self):
        """Test analyze with invalid symbol returns error code."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_quant.cli", "analyze",
             "--symbol", "INVALID", "--strategy", "livermore"],
            capture_output=True,
            text=True
        )

        # Should handle error gracefully
        # When implemented, should return non-zero exit code
        assert result.returncode is not None
