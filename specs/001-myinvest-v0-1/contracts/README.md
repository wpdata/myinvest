# API Contracts: MyInvest v0.1

**Date**: 2025-10-14
**Feature**: MyInvest v0.1 - Intelligent Investment Analysis System

## Overview

This directory contains API contracts for all investlib-* libraries and investapp. All contracts follow:
- Library-First principle (Constitution I)
- CLI Interface Mandate (Constitution II)
- JSON input/output for structured data
- `--dry-run` support for preview operations

## Contract Categories

1. **[data-import.md](data-import.md)** - CSV import and manual entry
2. **[market-data.md](market-data.md)** - Tushare/AKShare API integration
3. **[recommendations.md](recommendations.md)** - Livermore strategy and recommendations
4. **[operations.md](operations.md)** - Trade execution and logging

## CLI Command Patterns

All investlib-* libraries provide CLI commands following this pattern:

```bash
<library-name> <command> [options]

Options:
  --help          Show help message and exit
  --dry-run       Preview operation without executing
  --output FORMAT Output format: text|json (default: text)
```

## JSON Schema Validation

All JSON inputs/outputs use Python dataclasses with type validation:

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

@dataclass
class RecommendationRequest:
    symbol: str
    strategy: str = "livermore"

    def validate(self):
        assert len(self.symbol) == 9, "Symbol must be 9 characters (e.g., 600519.SH)"
```

## Error Handling

All CLI commands return:
- Exit code 0 on success
- Exit code 1 on user error (invalid input)
- Exit code 2 on system error (API failure, database error)
- JSON error format: `{"error": "message", "code": "ERROR_CODE"}`

## See Individual Contract Files

Detailed schemas and examples in individual .md files.
