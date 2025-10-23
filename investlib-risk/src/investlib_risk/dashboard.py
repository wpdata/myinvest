"""Risk Dashboard Orchestrator.

Coordinates all risk calculations and provides caching for dashboard refresh.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import threading
import time

from investlib_risk.var import (
    calculate_var_historical,
    calculate_cvar_historical,
    calculate_portfolio_returns_with_futures
)
from investlib_risk.correlation import CorrelationCalculator
from investlib_risk.concentration import (
    calculate_concentration,
    calculate_industry_concentration
)
from investlib_risk.margin_risk import (
    calculate_margin_usage_rate,
    generate_liquidation_warnings
)


logger = logging.getLogger(__name__)


class RiskDashboardOrchestrator:
    """Coordinate all risk metric calculations for dashboard."""

    def __init__(
        self,
        cache_ttl_seconds: int = 5,
        auto_refresh_interval: int = 5
    ):
        """Initialize risk dashboard orchestrator.

        Args:
            cache_ttl_seconds: Cache time-to-live (default 5s)
            auto_refresh_interval: Background refresh interval (default 5s)
        """
        self.cache_ttl = cache_ttl_seconds
        self.auto_refresh_interval = auto_refresh_interval

        # Initialize calculators
        self.corr_calc = CorrelationCalculator(cache_ttl_seconds=cache_ttl_seconds)

        # Cache
        self._metrics_cache = {}
        self._cache_timestamp = None

        # Background thread
        self._refresh_thread = None
        self._stop_refresh = threading.Event()

        self.logger = logging.getLogger(__name__)

    def calculate_all_metrics(
        self,
        portfolio: Dict,
        price_history: Optional[pd.DataFrame] = None,
        industry_map: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Calculate all risk metrics for portfolio.

        Args:
            portfolio: Dict with:
                - positions: List[Dict] with symbol, value, asset_type, etc.
                - account_balance: float
            price_history: DataFrame with [symbol, timestamp, close]
            industry_map: Dict mapping symbol to industry

        Returns:
            Dict with all risk metrics:
            - var_95: float
            - cvar_95: float
            - correlation_matrix: pd.DataFrame
            - high_correlation_pairs: List[Tuple]
            - concentration: Dict
            - industry_concentration: Dict
            - margin_usage_pct: float
            - liquidation_warnings: List[Dict]
            - greeks: Dict (if options exist)
            - calculated_at: datetime

        Example:
            >>> orchestrator = RiskDashboardOrchestrator()
            >>> metrics = orchestrator.calculate_all_metrics(portfolio, prices)
        """
        # Check cache
        if self._is_cache_valid():
            self.logger.debug("Using cached risk metrics")
            return self._metrics_cache

        self.logger.info("Calculating all risk metrics...")
        start_time = time.time()

        positions = portfolio.get('positions', [])
        account_balance = portfolio.get('account_balance', 0)

        metrics = {
            'calculated_at': datetime.now()
        }

        # 1. VaR and CVaR
        if price_history is not None and not price_history.empty:
            try:
                returns = calculate_portfolio_returns_with_futures(positions, price_history)
                metrics['var_95'] = calculate_var_historical(returns, confidence=0.95)
                metrics['cvar_95'] = calculate_cvar_historical(returns, confidence=0.95)
            except Exception as e:
                self.logger.warning(f"VaR calculation failed: {e}")
                metrics['var_95'] = 0.0
                metrics['cvar_95'] = 0.0
        else:
            metrics['var_95'] = 0.0
            metrics['cvar_95'] = 0.0

        # 2. Correlation matrix
        if price_history is not None and not price_history.empty:
            try:
                # Pivot price history to wide format
                prices_wide = price_history.pivot(
                    index='timestamp',
                    columns='symbol',
                    values='close'
                )
                metrics['correlation_matrix'] = self.corr_calc.calculate_correlation_matrix(
                    prices_wide,
                    window=60
                )
                metrics['high_correlation_pairs'] = self.corr_calc.highlight_high_correlation(
                    metrics['correlation_matrix'],
                    threshold=0.7
                )
            except Exception as e:
                self.logger.warning(f"Correlation calculation failed: {e}")
                metrics['correlation_matrix'] = pd.DataFrame()
                metrics['high_correlation_pairs'] = []
        else:
            metrics['correlation_matrix'] = pd.DataFrame()
            metrics['high_correlation_pairs'] = []

        # 3. Concentration risk
        try:
            metrics['concentration'] = calculate_concentration(positions)
            metrics['industry_concentration'] = calculate_industry_concentration(
                positions,
                industry_map
            )
        except Exception as e:
            self.logger.warning(f"Concentration calculation failed: {e}")
            metrics['concentration'] = {}
            metrics['industry_concentration'] = {}

        # 4. Margin risk
        try:
            metrics['margin_usage_pct'] = calculate_margin_usage_rate(
                positions,
                account_balance
            )

            # Get current prices for liquidation warnings
            current_prices = {}
            if price_history is not None and not price_history.empty:
                latest = price_history.sort_values('timestamp').groupby('symbol').last()
                current_prices = latest['close'].to_dict()

            metrics['liquidation_warnings'] = generate_liquidation_warnings(
                positions,
                current_prices,
                warning_threshold=5.0,
                critical_threshold=3.0
            )
        except Exception as e:
            self.logger.warning(f"Margin risk calculation failed: {e}")
            metrics['margin_usage_pct'] = 0.0
            metrics['liquidation_warnings'] = []

        # 5. Options Greeks aggregation
        try:
            from investlib_greeks.aggregator import aggregate_position_greeks

            option_positions = [p for p in positions if p.get('asset_type') == 'option']
            if option_positions:
                metrics['greeks'] = aggregate_position_greeks(option_positions)
            else:
                metrics['greeks'] = {
                    'total_delta': 0.0,
                    'total_gamma': 0.0,
                    'total_vega': 0.0,
                    'total_theta': 0.0,
                    'total_rho': 0.0
                }
        except Exception as e:
            self.logger.warning(f"Greeks aggregation failed: {e}")
            metrics['greeks'] = {}

        # Cache results
        self._metrics_cache = metrics
        self._cache_timestamp = datetime.now()

        elapsed = time.time() - start_time
        self.logger.info(f"Risk metrics calculated in {elapsed*1000:.0f}ms")

        return metrics

    def start_background_updates(
        self,
        portfolio_getter: callable,
        price_history_getter: callable,
        industry_map_getter: Optional[callable] = None
    ):
        """Start background thread for auto-refresh.

        Args:
            portfolio_getter: Function that returns current portfolio dict
            price_history_getter: Function that returns price history DataFrame
            industry_map_getter: Optional function that returns industry map
        """
        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            self.logger.warning("Background refresh already running")
            return

        self._stop_refresh.clear()

        def refresh_loop():
            while not self._stop_refresh.is_set():
                try:
                    portfolio = portfolio_getter()
                    price_history = price_history_getter()
                    industry_map = industry_map_getter() if industry_map_getter else None

                    self.calculate_all_metrics(portfolio, price_history, industry_map)

                except Exception as e:
                    self.logger.error(f"Background refresh error: {e}")

                # Wait for next refresh
                self._stop_refresh.wait(self.auto_refresh_interval)

        self._refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self._refresh_thread.start()

        self.logger.info(f"Background refresh started (interval: {self.auto_refresh_interval}s)")

    def stop_background_updates(self):
        """Stop background refresh thread."""
        if self._refresh_thread is None:
            return

        self._stop_refresh.set()
        self._refresh_thread.join(timeout=2)
        self._refresh_thread = None

        self.logger.info("Background refresh stopped")

    def _is_cache_valid(self) -> bool:
        """Check if cached metrics are still valid.

        Returns:
            True if cache exists and not expired
        """
        if not self._metrics_cache:
            return False

        if self._cache_timestamp is None:
            return False

        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self.cache_ttl

    def clear_cache(self):
        """Clear all cached metrics."""
        self._metrics_cache = {}
        self._cache_timestamp = None
        self.corr_calc.clear_cache()
        self.logger.info("Risk metrics cache cleared")
