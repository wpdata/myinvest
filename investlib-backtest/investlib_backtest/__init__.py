"""investlib-backtest: Historical Backtest Engine for MyInvest V0.2.

Provides comprehensive backtesting capabilities for investment strategies
using 3+ years of real historical market data.

Core Components:
- BacktestRunner: Main backtest execution engine
- Portfolio: Portfolio state tracking during backtest
- PerformanceMetrics: Calculate returns, Sharpe ratio, drawdown, etc.
- TradeAnalysis: Win rate, profit factor, trade distribution
- ReportGenerator: Generate HTML/JSON backtest reports
"""

__version__ = "0.2.0"

from investlib_backtest.engine.backtest_runner import BacktestRunner
from investlib_backtest.engine.portfolio import Portfolio
from investlib_backtest.metrics.performance import PerformanceMetrics
from investlib_backtest.metrics.trade_analysis import TradeAnalysis

__all__ = [
    'BacktestRunner',
    'Portfolio',
    'PerformanceMetrics',
    'TradeAnalysis',
]
