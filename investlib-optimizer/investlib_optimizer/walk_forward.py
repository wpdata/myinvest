"""
MyInvest V0.3 - Walk-Forward Validation (T021)
Rolling window train/test splits to detect overfitting.
"""

import logging
import pandas as pd
from typing import Dict, Tuple, List, Any
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class WalkForwardValidator:
    """Walk-forward validation framework.

    Splits data into rolling train/test windows to validate strategy
    robustness and detect overfitting.

    Standard configuration (from tasks.md):
    - Training period: 2 years
    - Testing period: 1 year
    - Walk forward: 3-year cycle

    Example:
        >>> validator = WalkForwardValidator()
        >>> train_metrics, test_metrics = validator.run_walk_forward(
        ...     strategy, data, best_params, train_period_days=730, test_period_days=365
        ... )
        >>> # Check for overfitting
        >>> if train_metrics['sharpe'] - test_metrics['sharpe'] > 0.5:
        ...     print("Warning: Overfitting detected!")
    """

    def __init__(self):
        """Initialize walk-forward validator."""
        self.validation_history = []

    def split_data(
        self,
        data: pd.DataFrame,
        train_period_days: int = 730,  # 2 years
        test_period_days: int = 365    # 1 year
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Split data into rolling train/test windows.

        Args:
            data: Market data DataFrame with 'timestamp' column
            train_period_days: Training window size in days (default: 730 = 2 years)
            test_period_days: Testing window size in days (default: 365 = 1 year)

        Returns:
            List of (train_data, test_data) tuples

        Raises:
            ValueError: If data insufficient for requested periods
        """
        if 'timestamp' not in data.columns:
            raise ValueError("Data must contain 'timestamp' column")

        # Sort by timestamp
        data = data.sort_values('timestamp').reset_index(drop=True)

        # Calculate total days required
        min_days = train_period_days + test_period_days
        actual_days = len(data)

        if actual_days < min_days:
            # Calculate date range of available data
            start_date = data['timestamp'].min()
            end_date = data['timestamp'].max()
            calendar_days = (end_date - start_date).days

            raise ValueError(
                f"Insufficient data: {actual_days} trading days available, "
                f"{min_days} trading days required ({train_period_days} train + {test_period_days} test).\n"
                f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} "
                f"({calendar_days} calendar days = ~{actual_days} trading days).\n"
                f"Suggestion: Either extend date range to get more data, or reduce train/test periods."
            )

        # Generate rolling windows
        splits = []
        start_idx = 0

        while start_idx + min_days <= len(data):
            train_end_idx = start_idx + train_period_days
            test_end_idx = train_end_idx + test_period_days

            train_data = data.iloc[start_idx:train_end_idx].copy()
            test_data = data.iloc[train_end_idx:test_end_idx].copy()

            splits.append((train_data, test_data))

            # Move window forward by test period (non-overlapping test sets)
            start_idx += test_period_days

        logger.info(
            f"[WalkForward] Created {len(splits)} train/test splits "
            f"(train={train_period_days}d, test={test_period_days}d)"
        )

        return splits

    def run_walk_forward(
        self,
        strategy_class,
        data: pd.DataFrame,
        param_combo: Dict[str, Any],
        symbol: str,
        capital: float = 100000.0,
        train_period_days: int = 730,
        test_period_days: int = 365
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Run walk-forward validation for a parameter combination.

        Args:
            strategy_class: Strategy class (not instance)
            data: Full market data
            param_combo: Parameter combination to test
            symbol: Stock symbol
            capital: Initial capital
            train_period_days: Training window days
            test_period_days: Testing window days

        Returns:
            Tuple of (train_metrics, test_metrics) where each is a dict with:
                - sharpe_ratio
                - total_return
                - max_drawdown_pct
                - total_trades

        Raises:
            ValueError: If validation fails
        """
        logger.info(
            f"[WalkForward] Running validation for {symbol} "
            f"with params: {param_combo}"
        )

        # Split data
        splits = self.split_data(data, train_period_days, test_period_days)

        if not splits:
            raise ValueError("No valid train/test splits generated")

        # Run backtest on each split
        from investlib_backtest.engine.backtest_runner import BacktestRunner

        runner = BacktestRunner(initial_capital=capital)

        train_results = []
        test_results = []

        for i, (train_data, test_data) in enumerate(splits):
            logger.debug(f"[WalkForward] Processing split {i+1}/{len(splits)}...")

            try:
                # Initialize strategy
                strategy_instance = strategy_class(**param_combo)

                # Train period
                train_start = train_data['timestamp'].min()
                train_end = train_data['timestamp'].max()

                train_result = runner.run_single_stock(
                    symbol=symbol,
                    data=train_data,
                    start_date=train_start,
                    end_date=train_end,
                    strategy=strategy_instance,
                    capital=capital
                )

                # Test period
                strategy_instance_test = strategy_class(**param_combo)
                test_start = test_data['timestamp'].min()
                test_end = test_data['timestamp'].max()

                test_result = runner.run_single_stock(
                    symbol=symbol,
                    data=test_data,
                    start_date=test_start,
                    end_date=test_end,
                    strategy=strategy_instance_test,
                    capital=capital
                )

                train_results.append(train_result)
                test_results.append(test_result)

            except Exception as e:
                logger.warning(f"[WalkForward] Split {i+1} failed: {e}")

        if not train_results or not test_results:
            raise ValueError("All walk-forward splits failed")

        # Aggregate metrics
        train_metrics = self._aggregate_metrics(train_results)
        test_metrics = self._aggregate_metrics(test_results)

        logger.info(
            f"[WalkForward] Validation complete: "
            f"Train Sharpe={train_metrics['sharpe_ratio']:.2f}, "
            f"Test Sharpe={test_metrics['sharpe_ratio']:.2f}"
        )

        # Store in history
        self.validation_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'params': param_combo,
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'splits_count': len(splits)
        })

        return train_metrics, test_metrics

    def _aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate metrics across multiple backtest results.

        Args:
            results: List of backtest results

        Returns:
            Dict with averaged metrics
        """
        from investlib_backtest.metrics.performance import PerformanceMetrics

        perf_metrics = PerformanceMetrics()

        all_sharpe = []
        all_returns = []
        all_drawdowns = []
        all_trades = []

        for result in results:
            try:
                metrics = perf_metrics.calculate_all_metrics(result)
                all_sharpe.append(metrics.get('sharpe_ratio', 0))
                all_returns.append(result.get('total_return', 0))
                all_drawdowns.append(metrics.get('max_drawdown_pct', 0))
                all_trades.append(result.get('total_trades', 0))
            except Exception as e:
                logger.warning(f"[WalkForward] Metric calculation failed: {e}")

        # Calculate averages
        return {
            'sharpe_ratio': sum(all_sharpe) / len(all_sharpe) if all_sharpe else 0,
            'total_return': sum(all_returns) / len(all_returns) if all_returns else 0,
            'max_drawdown_pct': sum(all_drawdowns) / len(all_drawdowns) if all_drawdowns else 0,
            'total_trades': sum(all_trades) / len(all_trades) if all_trades else 0,
            'sample_count': len(results)
        }

    def get_overfitting_score(
        self,
        train_metrics: Dict[str, float],
        test_metrics: Dict[str, float]
    ) -> float:
        """Calculate overfitting score (Sharpe divergence).

        Args:
            train_metrics: Training period metrics
            test_metrics: Testing period metrics

        Returns:
            Overfitting score (train_sharpe - test_sharpe)
            Higher values indicate more overfitting
        """
        train_sharpe = train_metrics.get('sharpe_ratio', 0)
        test_sharpe = test_metrics.get('sharpe_ratio', 0)

        divergence = train_sharpe - test_sharpe

        return divergence

    def is_overfitted(
        self,
        train_metrics: Dict[str, float],
        test_metrics: Dict[str, float],
        threshold: float = 0.5
    ) -> bool:
        """Check if strategy is overfitted.

        Args:
            train_metrics: Training metrics
            test_metrics: Testing metrics
            threshold: Divergence threshold (default: 0.5 from FR-017)

        Returns:
            True if overfitted (divergence > threshold)
        """
        divergence = self.get_overfitting_score(train_metrics, test_metrics)

        return divergence > threshold
