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
