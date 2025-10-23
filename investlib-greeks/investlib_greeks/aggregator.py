"""Aggregate Greeks across multiple option positions.

Calculates portfolio-level Greeks by summing individual position Greeks.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
import logging


logger = logging.getLogger(__name__)


def aggregate_position_greeks(positions: List[Dict]) -> Dict[str, float]:
    """Aggregate Greeks across all option positions.

    Args:
        positions: List of option position dicts with:
            - symbol: str
            - quantity: int
            - direction: 'long' | 'short' (long=+1, short=-1)
            - multiplier: int (e.g., 10000 for 50ETF options)
            - greeks: Dict with delta, gamma, vega, theta, rho

    Returns:
        Dict with aggregated Greeks:
        - total_delta: Portfolio delta
        - total_gamma: Portfolio gamma
        - total_vega: Portfolio vega
        - total_theta: Portfolio theta (daily decay)
        - total_rho: Portfolio rho

    Example:
        >>> positions = [
        ...     {'symbol': '10005102.SH', 'quantity': 2, 'direction': 'long',
        ...      'multiplier': 10000, 'greeks': {'delta': 0.5, 'gamma': 0.04, ...}},
        ...     {'symbol': '10005103.SH', 'quantity': 1, 'direction': 'short',
        ...      'multiplier': 10000, 'greeks': {'delta': -0.4, 'gamma': 0.05, ...}}
        ... ]
        >>> total_greeks = aggregate_position_greeks(positions)
        >>> # {'total_delta': 10400, 'total_gamma': 1300, ...}
    """
    if not positions:
        logger.warning("No positions provided")
        return {
            'total_delta': 0.0,
            'total_gamma': 0.0,
            'total_vega': 0.0,
            'total_theta': 0.0,
            'total_rho': 0.0
        }

    total_delta = 0.0
    total_gamma = 0.0
    total_vega = 0.0
    total_theta = 0.0
    total_rho = 0.0

    for pos in positions:
        if pos.get('asset_type') != 'option':
            continue

        quantity = pos.get('quantity', 0)
        direction = pos.get('direction', 'long')
        multiplier = pos.get('multiplier', 10000)
        greeks = pos.get('greeks', {})

        # Sign: long=+1, short=-1
        sign = 1 if direction == 'long' else -1

        # Aggregate each Greek
        # Delta: per-contract delta * quantity * multiplier * sign
        delta = greeks.get('delta', 0.0)
        total_delta += delta * quantity * multiplier * sign

        # Gamma: per-contract gamma * quantity * multiplier (always positive, no sign)
        gamma = greeks.get('gamma', 0.0)
        total_gamma += gamma * quantity * multiplier

        # Vega: per-contract vega * quantity * multiplier * sign
        vega = greeks.get('vega', 0.0)
        total_vega += vega * quantity * multiplier * sign

        # Theta: per-contract theta * quantity * multiplier * sign
        # Note: Theta is already negative for long options
        theta = greeks.get('theta', 0.0)
        total_theta += theta * quantity * multiplier * sign

        # Rho: per-contract rho * quantity * multiplier * sign
        rho = greeks.get('rho', 0.0)
        total_rho += rho * quantity * multiplier * sign

    aggregated = {
        'total_delta': total_delta,
        'total_gamma': total_gamma,
        'total_vega': total_vega,
        'total_theta': total_theta,
        'total_rho': total_rho
    }

    logger.info(
        f"Aggregated Greeks: Delta={total_delta:.0f}, Gamma={total_gamma:.0f}, "
        f"Vega={total_vega:.0f}, Theta={total_theta:.0f}/day"
    )

    return aggregated


def calculate_delta_hedge_ratio(
    portfolio_delta: float,
    underlying_price: float,
    underlying_multiplier: int = 1
) -> int:
    """Calculate number of underlying contracts needed to delta hedge.

    Args:
        portfolio_delta: Portfolio total delta
        underlying_price: Current underlying price
        underlying_multiplier: Underlying contract multiplier (1 for stocks, 300 for futures)

    Returns:
        Number of underlying contracts to hedge (negative = short, positive = long)

    Example:
        >>> # Portfolio delta = +5000 (net long)
        >>> # To hedge: short 5000 / (3000 * 1) = -1.67 ≈ -2 lots (200 shares)
        >>> contracts = calculate_delta_hedge_ratio(5000, 3000, multiplier=1)
        >>> # Returns -2 (need to short 200 shares to neutralize)
    """
    if underlying_price == 0:
        logger.warning("Underlying price is 0, cannot calculate hedge ratio")
        return 0

    # Delta hedge formula: contracts = -portfolio_delta / (price * multiplier)
    hedge_contracts = -portfolio_delta / (underlying_price * underlying_multiplier)

    # Round to nearest integer
    hedge_contracts_rounded = int(np.round(hedge_contracts))

    logger.info(
        f"Delta hedge: Portfolio Delta={portfolio_delta:.0f}, "
        f"Underlying={underlying_price:.2f}, Multiplier={underlying_multiplier} "
        f"→ Hedge with {hedge_contracts_rounded} contracts"
    )

    return hedge_contracts_rounded
