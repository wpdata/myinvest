"""Value at Risk (VaR) and Conditional VaR (CVaR) calculation.

Uses historical simulation method for portfolio risk estimation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


def calculate_var_historical(
    returns: pd.Series,
    confidence: float = 0.95,
    horizon: int = 1
) -> float:
    """Calculate VaR using historical simulation method.

    Args:
        returns: Series of historical returns
        confidence: Confidence level (default 0.95 = 95%)
        horizon: Time horizon in days (default 1)

    Returns:
        VaR value (negative indicates loss)

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.005])
        >>> var_95 = calculate_var_historical(returns, confidence=0.95)
        >>> # Returns 5th percentile (worst 5% of returns)
    """
    if returns.empty:
        logger.warning("Empty returns series, returning 0")
        return 0.0

    # Remove NaN values
    clean_returns = returns.dropna()

    if len(clean_returns) == 0:
        logger.warning("No valid returns after dropna, returning 0")
        return 0.0

    # Adjust for horizon (sqrt of time rule)
    if horizon > 1:
        adjusted_returns = clean_returns * np.sqrt(horizon)
    else:
        adjusted_returns = clean_returns

    # Calculate percentile (1 - confidence gives the tail)
    percentile = (1 - confidence) * 100
    var_value = np.percentile(adjusted_returns, percentile)

    logger.info(
        f"VaR calculated: {var_value:.4f} at {confidence*100}% confidence, "
        f"{horizon}-day horizon"
    )

    return var_value


def calculate_cvar_historical(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """Calculate Conditional VaR (Expected Shortfall).

    CVaR is the expected loss given that VaR is exceeded.

    Args:
        returns: Series of historical returns
        confidence: Confidence level (default 0.95)

    Returns:
        CVaR value (average of returns below VaR threshold)

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.005])
        >>> cvar_95 = calculate_cvar_historical(returns, confidence=0.95)
        >>> # Returns average of worst 5% returns
    """
    if returns.empty:
        logger.warning("Empty returns series, returning 0")
        return 0.0

    # Remove NaN values
    clean_returns = returns.dropna()

    if len(clean_returns) == 0:
        logger.warning("No valid returns after dropna, returning 0")
        return 0.0

    # First calculate VaR
    var_threshold = calculate_var_historical(clean_returns, confidence, horizon=1)

    # CVaR is the mean of returns below VaR threshold
    tail_returns = clean_returns[clean_returns <= var_threshold]

    if len(tail_returns) == 0:
        # No returns below threshold, return VaR itself
        cvar_value = var_threshold
    else:
        cvar_value = tail_returns.mean()

    logger.info(
        f"CVaR calculated: {cvar_value:.4f} at {confidence*100}% confidence "
        f"(VaR threshold: {var_threshold:.4f})"
    )

    return cvar_value


def calculate_portfolio_returns_with_futures(
    positions: List[Dict],
    price_history: pd.DataFrame
) -> pd.Series:
    """Calculate portfolio returns including futures leverage.

    Args:
        positions: List of position dicts with:
            - symbol: str
            - quantity: int
            - asset_type: 'stock' | 'futures' | 'option'
            - entry_price: float
            - For futures: multiplier, margin_rate
        price_history: DataFrame with columns [symbol, timestamp, close]

    Returns:
        Series of portfolio returns

    Example:
        >>> positions = [
        ...     {'symbol': '600519.SH', 'quantity': 100, 'asset_type': 'stock',
        ...      'entry_price': 1800, 'value': 180000},
        ...     {'symbol': 'IF2506.CFFEX', 'quantity': 1, 'asset_type': 'futures',
        ...      'entry_price': 4000, 'multiplier': 300, 'margin_rate': 0.15}
        ... ]
        >>> returns = calculate_portfolio_returns_with_futures(positions, price_df)
    """
    if not positions:
        logger.warning("No positions provided, returning empty series")
        return pd.Series(dtype=float)

    # Calculate total portfolio value
    total_value = 0.0
    for pos in positions:
        if pos['asset_type'] == 'stock':
            total_value += pos.get('value', pos['quantity'] * pos['entry_price'])
        elif pos['asset_type'] == 'futures':
            # Futures: margin as capital
            margin = pos['entry_price'] * pos['quantity'] * pos.get('multiplier', 300) * pos.get('margin_rate', 0.15)
            total_value += margin

    if total_value == 0:
        logger.warning("Total portfolio value is 0, returning empty series")
        return pd.Series(dtype=float)

    # Pivot price history
    price_pivot = price_history.pivot(index='timestamp', columns='symbol', values='close')

    # Calculate returns for each asset
    returns_df = price_pivot.pct_change()

    # Weight returns by position value
    portfolio_returns = pd.Series(0.0, index=returns_df.index)

    for pos in positions:
        symbol = pos['symbol']
        if symbol not in returns_df.columns:
            logger.warning(f"Symbol {symbol} not found in price history")
            continue

        # Calculate position weight
        if pos['asset_type'] == 'stock':
            position_value = pos.get('value', pos['quantity'] * pos['entry_price'])
            weight = position_value / total_value
            # Stock returns (no leverage)
            portfolio_returns += returns_df[symbol] * weight

        elif pos['asset_type'] == 'futures':
            # Futures: levered returns
            margin = pos['entry_price'] * pos['quantity'] * pos.get('multiplier', 300) * pos.get('margin_rate', 0.15)
            weight = margin / total_value
            leverage = 1 / pos.get('margin_rate', 0.15)  # e.g., 15% margin = 6.67x leverage
            # Futures returns are leveraged
            portfolio_returns += returns_df[symbol] * weight * leverage

    return portfolio_returns.dropna()
