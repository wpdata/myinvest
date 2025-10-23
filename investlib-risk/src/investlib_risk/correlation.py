"""Correlation matrix calculation with rolling windows and caching.

Calculates correlation between assets to identify concentration risk.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class CorrelationCalculator:
    """Rolling correlation calculator with built-in caching."""

    def __init__(self, cache_ttl_seconds: int = 5):
        """Initialize correlation calculator.

        Args:
            cache_ttl_seconds: Cache time-to-live in seconds (default 5s for dashboard)
        """
        self.cache_ttl = cache_ttl_seconds
        self._cache = {}
        self._cache_timestamps = {}
        self.logger = logging.getLogger(__name__)

    def calculate_correlation_matrix(
        self,
        prices_df: pd.DataFrame,
        window: int = 60
    ) -> pd.DataFrame:
        """Calculate rolling correlation matrix.

        Args:
            prices_df: DataFrame with columns=[symbol1, symbol2, ...], index=timestamp
            window: Rolling window in days (default 60)

        Returns:
            Correlation matrix DataFrame

        Example:
            >>> prices = pd.DataFrame({
            ...     '600519.SH': [1800, 1810, 1795, ...],
            ...     'IF2506.CFFEX': [4000, 4010, 3990, ...]
            ... })
            >>> calc = CorrelationCalculator()
            >>> corr_matrix = calc.calculate_correlation_matrix(prices, window=60)
            >>> # corr_matrix['600519.SH']['IF2506.CFFEX'] = -0.45
        """
        # Check cache
        cache_key = f"corr_{window}_{len(prices_df)}"
        if self._is_cache_valid(cache_key):
            self.logger.debug(f"Cache hit for correlation matrix (window={window})")
            return self._cache[cache_key]

        if prices_df.empty or len(prices_df) < window:
            self.logger.warning(
                f"Insufficient data for correlation: {len(prices_df)} rows < {window} window"
            )
            return pd.DataFrame()

        # Calculate returns
        returns = prices_df.pct_change().dropna()

        # Use last 'window' days for correlation
        if len(returns) > window:
            recent_returns = returns.tail(window)
        else:
            recent_returns = returns

        # Calculate correlation matrix
        corr_matrix = recent_returns.corr()

        # Cache result
        self._cache[cache_key] = corr_matrix
        self._cache_timestamps[cache_key] = datetime.now()

        self.logger.info(
            f"Correlation matrix calculated: {corr_matrix.shape[0]} assets, "
            f"{window}-day window"
        )

        return corr_matrix

    def highlight_high_correlation(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """Identify pairs with high correlation.

        Args:
            corr_matrix: Correlation matrix
            threshold: Correlation threshold (default 0.7)

        Returns:
            List of (symbol1, symbol2, correlation) tuples

        Example:
            >>> pairs = calc.highlight_high_correlation(corr_matrix, threshold=0.7)
            >>> # [('600519.SH', '000858.SZ', 0.85), ...]
        """
        high_corr_pairs = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                symbol1 = corr_matrix.columns[i]
                symbol2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]

                if abs(corr_value) >= threshold:
                    high_corr_pairs.append((symbol1, symbol2, corr_value))

        # Sort by absolute correlation (highest first)
        high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

        if high_corr_pairs:
            self.logger.info(
                f"Found {len(high_corr_pairs)} pairs with |correlation| >= {threshold}"
            )

        return high_corr_pairs

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid.

        Args:
            cache_key: Cache key

        Returns:
            True if cache is valid and not expired
        """
        if cache_key not in self._cache:
            return False

        if cache_key not in self._cache_timestamps:
            return False

        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self.cache_ttl

    def clear_cache(self):
        """Clear all cached correlation matrices."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.info("Correlation cache cleared")
