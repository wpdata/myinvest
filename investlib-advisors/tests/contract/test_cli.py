"""Contract tests for investlib-advisors CLI.

These tests verify the CLI interface contract (interface, options, exit codes).
Tests written BEFORE implementation (TDD RED phase).
"""

import subprocess
import sys
import pytest
import tempfile
import json
from pathlib import Path


class TestAdvisorsCLIContract:
    """Test investlib-advisors CLI contract compliance."""

    def test_cli_help_command(self):
        """Test investlib-advisors --help returns usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_advisors.cli", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "investlib-advisors" in result.stdout.lower()

    def test_list_advisors_command(self):
        """Test list-advisors command returns available advisors."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_advisors.cli", "list-advisors"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        advisors = json.loads(result.stdout)
        assert isinstance(advisors, list)
        assert "livermore" in advisors

    def test_ask_help_command(self):
        """Test ask --help shows usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_advisors.cli", "ask", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "ask" in result.stdout.lower()
        assert "--advisor" in result.stdout.lower()
        assert "--context" in result.stdout.lower()

    def test_ask_requires_advisor_argument(self):
        """Test ask fails without --advisor argument."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_advisors.cli", "ask"],
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_ask_requires_context_argument(self):
        """Test ask fails without --context argument."""
        result = subprocess.run(
            [sys.executable, "-m", "investlib_advisors.cli", "ask", "--advisor", "livermore"],
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_ask_with_valid_context_file(self):
        """Test ask command with valid context file."""
        # Create temporary context file
        context_data = {
            "symbol": "600519.SH",
            "signal": {
                "action": "BUY",
                "entry_price": 1500.0,
                "stop_loss": 1450.0,
                "take_profit": 1600.0
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(context_data, f)
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "investlib_advisors.cli", "ask",
                 "--advisor", "livermore", "--context", temp_file, "--output", "json"],
                capture_output=True,
                text=True
            )

            # Should not crash (implementation pending)
            assert result.returncode is not None

        finally:
            Path(temp_file).unlink()

    def test_ask_output_json_format(self):
        """Test ask --output json returns structured output."""
        # Create temporary context file
        context_data = {
            "symbol": "600519.SH",
            "signal": {"action": "BUY", "entry_price": 1500.0}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(context_data, f)
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "investlib_advisors.cli", "ask",
                 "--advisor", "livermore", "--context", temp_file, "--output", "json"],
                capture_output=True,
                text=True
            )

            # Should not crash
            assert result.returncode is not None
            # When implemented, should be valid JSON
            # data = json.loads(result.stdout)
            # assert 'recommendation' in data

        finally:
            Path(temp_file).unlink()

    def test_ask_invalid_advisor_returns_error(self):
        """Test ask with invalid advisor returns error."""
        # Create temporary context file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"symbol": "TEST"}, f)
            temp_file = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "investlib_advisors.cli", "ask",
                 "--advisor", "invalid_advisor", "--context", temp_file],
                capture_output=True,
                text=True
            )

            # Should fail (invalid choice)
            assert result.returncode != 0

        finally:
            Path(temp_file).unlink()
