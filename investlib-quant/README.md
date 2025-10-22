# investlib-quant

Quantitative strategy analysis and trading signal generation.

## Features

- Livermore trend-following strategy
- Technical indicator calculation (MA, MACD, ATR)
- Signal generation with risk management
- Position sizing calculator

## CLI Commands

```bash
# Analyze stock with Livermore strategy
investlib-quant analyze --symbol 600519.SH --strategy livermore --output json

# Generate trading signals
investlib-quant signals --input market_data.json --dry-run
```
