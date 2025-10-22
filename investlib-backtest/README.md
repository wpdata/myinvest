# investlib-backtest

Historical backtest engine for MyInvest V0.2.

## Features

- **Backtest Runner**: Execute strategies on 3+ years of historical data
- **Portfolio Tracking**: Simulate trades with realistic transaction costs
- **Performance Metrics**: Calculate Sharpe ratio, max drawdown, annualized returns
- **Trade Analysis**: Win rate, profit factor, trade distribution
- **Data Validation**: Ensure data quality before backtest execution

## Installation

```bash
cd investlib-backtest
pip install -e .
```

## Usage

### Python API

```python
from investlib_backtest import BacktestRunner, PerformanceMetrics
from investlib_quant.livermore_strategy import LivermoreStrategy

# Initialize strategy and runner
strategy = LivermoreStrategy()
runner = BacktestRunner(initial_capital=100000)

# Run backtest
results = runner.run(
    strategy=strategy,
    symbols=["600519.SH"],
    start_date="2022-01-01",
    end_date="2024-12-31"
)

# Calculate metrics
metrics = PerformanceMetrics()
performance = metrics.calculate_all_metrics(results)

print(f"Total Return: {performance['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {performance['max_drawdown_pct']:.2f}%")
```

### Components

#### BacktestRunner
Core engine for running backtests on historical data.

```python
runner = BacktestRunner(
    initial_capital=100000,
    commission_rate=0.0003,  # 0.03%
    slippage_rate=0.001       # 0.1%
)
```

#### Portfolio
Tracks cash, positions, and executes trades with transaction costs.

```python
from investlib_backtest.engine.portfolio import Portfolio

portfolio = Portfolio(initial_capital=100000)
portfolio.buy(symbol="600519.SH", price=1680, quantity=50, timestamp="2024-01-15")
portfolio.sell(symbol="600519.SH", price=1750, quantity=50, timestamp="2024-02-15")
```

#### PerformanceMetrics
Calculate investment performance metrics.

```python
from investlib_backtest.metrics.performance import PerformanceMetrics

metrics = PerformanceMetrics(risk_free_rate=0.03)
sharpe = metrics.calculate_sharpe_ratio(equity_curve)
drawdown = metrics.calculate_max_drawdown(equity_curve)
```

#### TradeAnalysis
Analyze trade execution and profitability.

```python
from investlib_backtest.metrics.trade_analysis import TradeAnalysis

analyzer = TradeAnalysis()
win_rate = analyzer.calculate_win_rate(trade_log)
profit_factor = analyzer.calculate_profit_factor(trade_log)
```

## Testing

```bash
pytest tests/
```

## License

MIT
