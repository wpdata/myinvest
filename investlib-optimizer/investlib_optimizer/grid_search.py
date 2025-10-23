"""
MyInvest V0.3 - Grid Search Parameter Optimization (T020)
Exhaustive parameter space exploration with parallel execution.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from itertools import product
from datetime import datetime


logger = logging.getLogger(__name__)


class GridSearchOptimizer:
    """Grid search parameter optimization engine.

    Exhaustively tests all parameter combinations in the defined space.
    Leverages parallel backtest for efficiency.

    Example:
        >>> optimizer = GridSearchOptimizer()
        >>> param_space = {
        ...     'stop_loss_pct': [5, 10, 15, 20, 25, 30, 35],
        ...     'take_profit_pct': [10, 15, 20, 25, 30, 35, 40, 45],
        ...     'position_size_pct': [10, 15, 20, 25, 30, 35, 40]
        ... }
        >>> results = optimizer.run_grid_search(
        ...     strategy, symbol, data, param_space
        ... )
        >>> # Results: 7×8×7 = 392 combinations
    """

    def __init__(self):
        """Initialize grid search optimizer."""
        self.results_history = []

    def define_parameter_space(
        self,
        param_ranges: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        """Define parameter space for grid search.

        Args:
            param_ranges: Dict mapping parameter name → list of values
                Example: {'stop_loss_pct': [5, 10, 15], 'take_profit_pct': [10, 20, 30]}

        Returns:
            Validated parameter space

        Raises:
            ValueError: If parameter ranges invalid
        """
        # Validate param_ranges
        if not param_ranges:
            raise ValueError("Parameter ranges cannot be empty")

        for param_name, values in param_ranges.items():
            if not values:
                raise ValueError(f"Parameter '{param_name}' has no values")

            if not all(isinstance(v, (int, float)) for v in values):
                raise ValueError(f"Parameter '{param_name}' contains non-numeric values")

        # Log parameter space size
        total_combinations = np.prod([len(values) for values in param_ranges.values()])
        logger.info(
            f"[GridSearch] Parameter space defined: {total_combinations} combinations "
            f"({' × '.join([f'{len(v)}' for v in param_ranges.values()])})"
        )

        return param_ranges

    def run_grid_search(
        self,
        strategy,
        symbol: str,
        data: pd.DataFrame,
        param_space: Dict[str, List[float]],
        start_date: str,
        end_date: str,
        capital: float = 100000.0,
        metric: str = 'sharpe_ratio'
    ) -> pd.DataFrame:
        """Run grid search optimization.

        Tests all parameter combinations and returns ranked results.

        Args:
            strategy: Strategy class (not instance)
            symbol: Stock symbol
            data: Market data DataFrame
            param_space: Parameter ranges dict
            start_date: Backtest start date
            end_date: Backtest end date
            capital: Initial capital
            metric: Optimization metric (default: 'sharpe_ratio')

        Returns:
            DataFrame with columns: [params, sharpe_ratio, total_return, max_drawdown, ...]
            Sorted by metric (best first)

        Raises:
            ValueError: If optimization fails
        """
        start_time = datetime.now()

        logger.info(
            f"[GridSearch] Starting grid search for {symbol} "
            f"from {start_date} to {end_date}"
        )

        # Generate all parameter combinations
        param_names = list(param_space.keys())
        param_values = [param_space[name] for name in param_names]
        all_combinations = list(product(*param_values))

        logger.info(f"[GridSearch] Testing {len(all_combinations)} parameter combinations...")

        # Run backtest for each combination
        from investlib_backtest.engine.backtest_runner import BacktestRunner

        runner = BacktestRunner(initial_capital=capital)
        results = []

        for i, combo in enumerate(all_combinations):
            # Create parameter dict
            params = {param_names[j]: combo[j] for j in range(len(param_names))}

            try:
                # Initialize strategy with these parameters
                strategy_instance = strategy(**params)

                # Run backtest
                result = runner.run_single_stock(
                    symbol=symbol,
                    data=data,
                    start_date=start_date,
                    end_date=end_date,
                    strategy=strategy_instance,
                    capital=capital
                )

                # Calculate metrics
                metrics = self._calculate_metrics(result)

                # Store result
                results.append({
                    **params,
                    **metrics,
                    'combination_id': i + 1
                })

                # Progress logging
                if (i + 1) % 50 == 0 or (i + 1) == len(all_combinations):
                    progress = (i + 1) / len(all_combinations) * 100
                    logger.info(
                        f"[GridSearch] Progress: {progress:.1f}% ({i+1}/{len(all_combinations)})"
                    )

            except Exception as e:
                logger.warning(f"[GridSearch] Failed for params {params}: {e}")
                # Store failed result
                results.append({
                    **params,
                    'sharpe_ratio': -999,
                    'total_return': -999,
                    'max_drawdown_pct': 100,
                    'error': str(e),
                    'combination_id': i + 1
                })

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Sort by metric (descending for sharpe/return, ascending for drawdown)
        if metric in ['sharpe_ratio', 'total_return', 'sortino_ratio']:
            results_df = results_df.sort_values(metric, ascending=False)
        elif metric in ['max_drawdown_pct']:
            results_df = results_df.sort_values(metric, ascending=True)

        # Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(
            f"[GridSearch] Completed in {duration:.1f}s: "
            f"{len(results_df)} combinations tested"
        )

        # Store in history
        self.results_history.append({
            'timestamp': start_time,
            'symbol': symbol,
            'results': results_df,
            'duration_seconds': duration
        })

        return results_df

    def _calculate_metrics(self, backtest_result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance metrics from backtest result.

        Args:
            backtest_result: Result from BacktestRunner.run_single_stock()

        Returns:
            Dict with sharpe_ratio, total_return, max_drawdown_pct, etc.
        """
        from investlib_backtest.metrics.performance import PerformanceMetrics

        perf_metrics = PerformanceMetrics()

        try:
            # Calculate all metrics
            metrics = perf_metrics.calculate_all_metrics(backtest_result)

            return {
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'sortino_ratio': metrics.get('sortino_ratio', 0),
                'total_return': backtest_result.get('total_return', 0),
                'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                'total_trades': backtest_result.get('total_trades', 0),
                'win_rate': metrics.get('win_rate', 0),
                'annualized_return': metrics.get('annualized_return', 0),
                'annualized_volatility': metrics.get('annualized_volatility', 0)
            }
        except Exception as e:
            logger.warning(f"[GridSearch] Metric calculation failed: {e}")
            return {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'total_return': 0,
                'max_drawdown_pct': 0,
                'total_trades': 0,
                'win_rate': 0,
                'annualized_return': 0,
                'annualized_volatility': 0
            }

    def get_best_parameters(
        self,
        results_df: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        top_n: int = 1
    ) -> List[Dict[str, Any]]:
        """Get best parameter combinations from results.

        Args:
            results_df: Results DataFrame from run_grid_search()
            metric: Optimization metric
            top_n: Number of top results to return

        Returns:
            List of parameter dicts (best first)
        """
        # Filter out failed results
        valid_results = results_df[results_df[metric] != -999]

        if valid_results.empty:
            logger.warning("[GridSearch] No valid results found")
            return []

        # Get top N
        top_results = valid_results.head(top_n)

        # Extract parameter columns (exclude metrics)
        metric_cols = ['sharpe_ratio', 'sortino_ratio', 'total_return', 'max_drawdown_pct',
                       'total_trades', 'win_rate', 'annualized_return', 'annualized_volatility',
                       'combination_id', 'error']

        param_cols = [col for col in top_results.columns if col not in metric_cols]

        # Build result list
        best_params = []
        for _, row in top_results.iterrows():
            params = {col: row[col] for col in param_cols}
            params['metrics'] = {col: row[col] for col in metric_cols if col in row.index and pd.notna(row[col])}
            best_params.append(params)

        return best_params

    def get_optimization_summary(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics from grid search results.

        Args:
            results_df: Results DataFrame

        Returns:
            Summary dict with best/worst/avg metrics
        """
        valid_results = results_df[results_df['sharpe_ratio'] != -999]

        if valid_results.empty:
            return {
                'total_combinations': len(results_df),
                'valid_combinations': 0,
                'failed_combinations': len(results_df)
            }

        return {
            'total_combinations': len(results_df),
            'valid_combinations': len(valid_results),
            'failed_combinations': len(results_df) - len(valid_results),
            'best_sharpe': valid_results['sharpe_ratio'].max(),
            'worst_sharpe': valid_results['sharpe_ratio'].min(),
            'avg_sharpe': valid_results['sharpe_ratio'].mean(),
            'best_return': valid_results['total_return'].max(),
            'worst_return': valid_results['total_return'].min(),
            'avg_return': valid_results['total_return'].mean()
        }
