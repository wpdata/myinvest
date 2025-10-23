# Multi-Asset Backtest Usage Guide (V0.3)

This guide explains how to use the new multi-asset backtesting features added in MyInvest V0.3.

## Overview

The multi-asset backtest engine supports:
- **Stocks**: Traditional equity trading (full payment)
- **Futures**: Margin-based trading with forced liquidation (T037, T038)
- **Options**: Premium-based trading with Greeks tracking

## Quick Start

```python
from investlib_backtest.engine import MultiAssetBacktestRunner
from investlib_quant.strategies import YourStrategy

# Initialize runner
runner = MultiAssetBacktestRunner(
    initial_capital=100000.0,
    commission_rate=0.0003,      # 0.03%
    slippage_rate=0.001,          # 0.1%
    force_close_margin_rate=0.03  # 3% for forced liquidation
)

# Define mixed portfolio
symbols = [
    '600519.SH',      # Stock: Moutai
    'IF2506.CFFEX',   # Futures: CSI 300 Index Futures
    '10005102.SH'     # Option: 50ETF Option
]

# Run backtest
strategy = YourStrategy()
results = runner.run(
    strategy=strategy,
    symbols=symbols,
    start_date='2024-01-01',
    end_date='2024-12-31',
    capital=100000.0
)

# Check results
print(f"Total Return: {results['total_return']*100:.2f}%")
print(f"Total Trades: {results['total_trades']}")
print(f"Forced Liquidations: {results['forced_liquidations']}")
print(f"Margin Used: {results['margin_stats']['margin_used']:.2f}")
```

## Asset Type Detection

The system automatically detects asset types from symbol patterns:

```python
from investlib_data.multi_asset_api import detect_asset_type

# Stock symbols
detect_asset_type('600519.SH')    # => 'stock'
detect_asset_type('000001.SZ')    # => 'stock'

# Futures symbols
detect_asset_type('IF2506.CFFEX')  # => 'futures'
detect_asset_type('IC2503.CFFEX')  # => 'futures'

# Options symbols
detect_asset_type('10005102.SH')   # => 'option'
```

### Symbol Patterns

- **Stock**: `XXXXXX.SH` or `XXXXXX.SZ` (6 digits)
- **Futures**: `LLDDMM.EXCHANGE` (letters + 4 digits + exchange)
  - Exchanges: CFFEX, DCE, CZCE, SHFE, INE
  - Example: `IF2506.CFFEX` = IF product, expires 2025-06
- **Options**: `10XXXXXX.SH` (starts with 10)

## Margin Management (Futures)

### How Margin Works

1. **Initial Margin**: When buying futures, only margin is required (not full payment)
   ```
   Margin = Price × Quantity × Multiplier × Margin Rate
   ```

2. **Margin Rate**: Typically 10-20% for Chinese futures
   - Stock index futures (IF, IC, IH): 15%
   - Commodity futures: varies by exchange

3. **Multiplier**:
   - CSI 300 futures (IF): 300
   - CSI 500 futures (IC): 200
   - Commodity futures: 100

### Example: Buying Futures

```python
# IF2506.CFFEX @ 4000 points
# Want to buy 1 contract with 15% margin

Price: 4000
Multiplier: 300
Margin Rate: 15%

Required Margin = 4000 × 1 × 300 × 0.15 = 180,000 CNY

# With 200,000 capital, you can buy 1 contract
# Remaining margin available: 20,000 CNY
```

## Forced Liquidation (T038)

The system automatically checks for forced liquidation **before** generating new signals each day.

### Liquidation Trigger

Forced liquidation occurs when:
```
Current Price ≤ Liquidation Price

Where:
Liquidation Price = Entry Price × (1 - (Margin Rate - Force Close Margin Rate))

Example:
Entry Price: 4000
Margin Rate: 15% (0.15)
Force Close Rate: 3% (0.03)

Liquidation Price = 4000 × (1 - (0.15 - 0.03))
                  = 4000 × 0.88
                  = 3520

If price drops to 3520 or below → FORCED LIQUIDATION
```

### Forced Liquidation Process

1. **Detection**: Every trading day, the system checks all futures positions
2. **Calculation**: Compares current price vs. liquidation price
3. **Execution**: If triggered, immediately closes the position
4. **Logging**: Records as forced liquidation in trade log
5. **Margin Release**: Releases margin back to available capital

### Trade Log Example

```python
{
    "timestamp": "2024-06-15",
    "symbol": "IF2506.CFFEX",
    "asset_type": "futures",
    "action": "SELL",
    "price": 3520.0,
    "quantity": 1,
    "is_forced_liquidation": true,
    "liquidation_reason": "Margin insufficient: price 3520.00 <= liquidation 3520.00",
    "margin_required": -180000.0  # Negative = released
}
```

## Greeks Tracking (Options)

For option positions, the system tracks:
- **Delta**: Price sensitivity (0 to 1 for calls, -1 to 0 for puts)
- **Gamma**: Delta sensitivity
- **Vega**: Volatility sensitivity
- **Theta**: Time decay

```python
# Example: Buying a call option
trade = {
    "symbol": "10005102.SH",
    "asset_type": "option",
    "action": "BUY",
    "delta": 0.58,
    "gamma": 0.04,
    "vega": 0.15,
    "theta": -0.05
}
```

## Result Structure

```python
{
    'strategy_name': 'YourStrategy',
    'symbols': ['600519.SH', 'IF2506.CFFEX'],
    'asset_types': {
        '600519.SH': 'stock',
        'IF2506.CFFEX': 'futures'
    },
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
    'initial_capital': 100000.0,
    'final_capital': 115230.45,
    'total_return': 0.1523,  # 15.23%
    'total_trades': 45,
    'signals_generated': 250,
    'forced_liquidations': 2,  # Number of forced liquidations
    'trade_log': [...],
    'equity_curve': [...],
    'margin_stats': {
        'margin_used': 50000.0,      # Currently locked
        'margin_available': 65230.45  # Available for new positions
    }
}
```

## Best Practices

### 1. Capital Allocation

```python
# Conservative: Reserve 50% for margin
total_capital = 200000
max_margin_usage = 100000  # 50%

# Aggressive: Use 80% for margin
max_margin_usage = 160000  # 80%
```

### 2. Risk Management

```python
# Set appropriate margin rates
force_close_margin_rate = 0.05  # 5% buffer (more conservative)
# vs
force_close_margin_rate = 0.03  # 3% buffer (default)
```

### 3. Position Sizing

```python
# For futures: limit to 1-2 contracts per signal
position_size_pct = 20  # 20% of capital per position

# For stocks: traditional sizing
position_size_pct = 10  # 10% of capital per position
```

## Data Sources

The system automatically routes to appropriate data sources:

- **Stocks**: Efinance → AKShare → Cache
- **Futures**: FuturesClient (AKShare) → Cache
- **Options**: OptionsClient (AKShare) → Cache

All data fetching uses the `MarketDataFetcher` with automatic fallback.

## Integration with Watchlist

The watchlist UI now shows asset type badges:

```
🟢 600519.SH    | 📈 股票   | 📁 核心持仓
🟢 IF2506.CFFEX | 📊 期货   | 📁 对冲
🟢 10005102.SH  | 📉 期权   | 📁 期权策略
```

## Dependencies

Make sure you have installed:

```bash
# Required for multi-asset support
pip install investlib-margin     # Margin calculator
pip install investlib-greeks     # Options Greeks calculator
pip install investlib-data       # Multi-asset data fetcher
```

## See Also

- `investlib-margin/investlib_margin/calculator.py` - Margin calculation
- `investlib-greeks/investlib_greeks/calculator.py` - Greeks calculation
- `investlib-data/investlib_data/multi_asset_api.py` - Asset type detection
- `investlib-backtest/investlib_backtest/engine/multi_asset_portfolio.py` - Portfolio implementation

---

**Note**: This is a V0.3 feature. Forced liquidation (T038) is automatically enabled in `MultiAssetBacktestRunner`.
