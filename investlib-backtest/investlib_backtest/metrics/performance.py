"""Performance metrics calculator (T068).

Calculates investment performance metrics:
- Total Return, Annualized Return
- Maximum Drawdown
- Sharpe Ratio, Sortino Ratio
- Volatility metrics
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional


class PerformanceMetrics:
    """Calculate portfolio performance metrics."""

    def __init__(self, risk_free_rate: float = 0.03):
        """Initialize performance metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate (default 3%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_total_return(
        self,
        initial_capital: float,
        final_capital: float
    ) -> float:
        """Calculate total return percentage.

        Args:
            initial_capital: Starting capital
            final_capital: Ending capital

        Returns:
            Total return as decimal (e.g., 0.25 = 25%)
        """
        return (final_capital - initial_capital) / initial_capital

    def calculate_annualized_return(
        self,
        total_return: float,
        years: float
    ) -> float:
        """Calculate annualized return (CAGR).

        Args:
            total_return: Total return as decimal
            years: Number of years

        Returns:
            Annualized return as decimal
        """
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1

    def calculate_max_drawdown(
        self,
        equity_curve: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate maximum drawdown from equity curve.

        Args:
            equity_curve: List of {date, value} dictionaries

        Returns:
            Dict with max_drawdown, peak_date, trough_date, recovery_date
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'peak_value': 0.0,
                'trough_value': 0.0,
                'peak_date': None,
                'trough_date': None,
                'recovery_date': None
            }

        values = [point['value'] for point in equity_curve]
        dates = [point['date'] for point in equity_curve]

        # Calculate running maximum
        running_max = np.maximum.accumulate(values)

        # Calculate drawdown at each point
        drawdowns = (values - running_max) / running_max

        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdowns)
        max_dd = drawdowns[max_dd_idx]

        # Find peak before max drawdown
        peak_idx = np.argmax(running_max[:max_dd_idx + 1])

        # Find recovery date (when equity exceeds previous peak)
        recovery_idx = None
        peak_value = values[peak_idx]
        for i in range(max_dd_idx + 1, len(values)):
            if values[i] >= peak_value:
                recovery_idx = i
                break

        return {
            'max_drawdown': abs(max_dd),  # As positive decimal
            'max_drawdown_pct': abs(max_dd) * 100,  # As percentage
            'peak_value': values[peak_idx],
            'trough_value': values[max_dd_idx],
            'peak_date': dates[peak_idx],
            'trough_date': dates[max_dd_idx],
            'recovery_date': dates[recovery_idx] if recovery_idx else None
        }

    def calculate_sharpe_ratio(
        self,
        equity_curve: List[Dict[str, Any]],
        trading_days_per_year: int = 252
    ) -> float:
        """Calculate Sharpe Ratio.

        Args:
            equity_curve: List of {date, value} dictionaries
            trading_days_per_year: Number of trading days per year

        Returns:
            Sharpe ratio
        """
        if len(equity_curve) < 2:
            return 0.0

        values = [point['value'] for point in equity_curve]

        # Calculate daily returns
        returns = pd.Series(values).pct_change().dropna()

        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # Annualized metrics
        mean_return = returns.mean() * trading_days_per_year
        std_return = returns.std() * np.sqrt(trading_days_per_year)

        # Sharpe ratio = (portfolio return - risk-free rate) / volatility
        sharpe = (mean_return - self.risk_free_rate) / std_return

        return sharpe

    def calculate_sortino_ratio(
        self,
        equity_curve: List[Dict[str, Any]],
        trading_days_per_year: int = 252
    ) -> float:
        """Calculate Sortino Ratio (uses only downside deviation).

        Args:
            equity_curve: List of {date, value} dictionaries
            trading_days_per_year: Number of trading days per year

        Returns:
            Sortino ratio
        """
        if len(equity_curve) < 2:
            return 0.0

        values = [point['value'] for point in equity_curve]
        returns = pd.Series(values).pct_change().dropna()

        if len(returns) == 0:
            return 0.0

        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        mean_return = returns.mean() * trading_days_per_year
        downside_std = downside_returns.std() * np.sqrt(trading_days_per_year)

        sortino = (mean_return - self.risk_free_rate) / downside_std

        return sortino

    def calculate_volatility(
        self,
        equity_curve: List[Dict[str, Any]],
        trading_days_per_year: int = 252
    ) -> Dict[str, float]:
        """Calculate volatility metrics.

        Args:
            equity_curve: List of {date, value} dictionaries
            trading_days_per_year: Number of trading days per year

        Returns:
            Dict with daily and annualized volatility
        """
        if len(equity_curve) < 2:
            return {'daily_volatility': 0.0, 'annualized_volatility': 0.0}

        values = [point['value'] for point in equity_curve]
        returns = pd.Series(values).pct_change().dropna()

        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(trading_days_per_year)

        return {
            'daily_volatility': daily_vol,
            'annualized_volatility': annual_vol
        }

    def calculate_all_metrics(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate all performance metrics from backtest results.

        Args:
            backtest_results: Results from BacktestRunner.run()

        Returns:
            Complete metrics dictionary
        """
        initial_capital = backtest_results['initial_capital']
        final_capital = backtest_results['final_capital']
        equity_curve = backtest_results['equity_curve']

        # Calculate time period
        start_date = pd.to_datetime(backtest_results['start_date'])
        end_date = pd.to_datetime(backtest_results['end_date'])
        years = (end_date - start_date).days / 365.25

        # Basic returns
        total_return = self.calculate_total_return(initial_capital, final_capital)
        annualized_return = self.calculate_annualized_return(total_return, years)

        # Drawdown analysis
        drawdown_metrics = self.calculate_max_drawdown(equity_curve)

        # Risk-adjusted returns
        sharpe_ratio = self.calculate_sharpe_ratio(equity_curve)
        sortino_ratio = self.calculate_sortino_ratio(equity_curve)

        # Volatility
        volatility = self.calculate_volatility(equity_curve)

        return {
            # Returns
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'annualized_return': annualized_return,
            'annualized_return_pct': annualized_return * 100,

            # Drawdown
            'max_drawdown': drawdown_metrics['max_drawdown'],
            'max_drawdown_pct': drawdown_metrics['max_drawdown_pct'],
            'peak_value': drawdown_metrics['peak_value'],
            'trough_value': drawdown_metrics['trough_value'],
            'peak_date': drawdown_metrics['peak_date'],
            'trough_date': drawdown_metrics['trough_date'],
            'recovery_date': drawdown_metrics['recovery_date'],

            # Risk-adjusted
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,

            # Volatility
            'daily_volatility': volatility['daily_volatility'],
            'annualized_volatility': volatility['annualized_volatility'],

            # Period
            'years': years,
            'trading_days': len(equity_curve)
        }
