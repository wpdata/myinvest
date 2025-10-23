"""Margin risk assessment for futures and options positions.

Calculates margin usage, liquidation distance, and generates warnings.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


def calculate_margin_usage_rate(
    positions: List[Dict],
    account_balance: float
) -> float:
    """Calculate margin usage rate.

    Args:
        positions: List of futures/options positions with margin_used field
        account_balance: Total account balance

    Returns:
        Margin usage percentage (0-100)

    Example:
        >>> positions = [
        ...     {'symbol': 'IF2506.CFFEX', 'margin_used': 180000, 'asset_type': 'futures'},
        ...     {'symbol': 'IC2503.CFFEX', 'margin_used': 120000, 'asset_type': 'futures'}
        ... ]
        >>> usage = calculate_margin_usage_rate(positions, account_balance=500000)
        >>> # Returns 60.0 (300000 / 500000 = 60%)
    """
    if account_balance <= 0:
        logger.warning("Account balance is 0 or negative")
        return 0.0

    # Sum margin used for futures/options positions
    total_margin_used = 0.0
    for pos in positions:
        if pos.get('asset_type') in ['futures', 'option']:
            total_margin_used += pos.get('margin_used', 0.0)

    usage_rate = (total_margin_used / account_balance) * 100

    logger.info(
        f"Margin usage: {total_margin_used:,.0f} / {account_balance:,.0f} = {usage_rate:.1f}%"
    )

    return usage_rate


def calculate_liquidation_distance(
    position: Dict,
    current_price: float
) -> float:
    """Calculate distance to forced liquidation.

    Args:
        position: Futures position dict with:
            - entry_price: float
            - direction: 'long' | 'short'
            - margin_rate: float (e.g., 0.15)
            - force_close_margin_rate: float (e.g., 0.03)
        current_price: Current market price

    Returns:
        Distance to liquidation as percentage (positive = safe, negative = already liquidated)

    Example:
        >>> position = {
        ...     'symbol': 'IF2506.CFFEX',
        ...     'entry_price': 4000,
        ...     'direction': 'long',
        ...     'margin_rate': 0.15,
        ...     'force_close_margin_rate': 0.03
        ... }
        >>> distance = calculate_liquidation_distance(position, current_price=3900)
        >>> # Returns percentage distance to liquidation price
    """
    entry_price = position.get('entry_price', 0)
    direction = position.get('direction', 'long')
    margin_rate = position.get('margin_rate', 0.15)
    force_close_rate = position.get('force_close_margin_rate', 0.03)

    if entry_price == 0:
        logger.warning("Entry price is 0, cannot calculate liquidation distance")
        return 0.0

    # Calculate liquidation price using investlib-margin formula
    from investlib_margin.calculator import MarginCalculator

    calc = MarginCalculator()
    liquidation_price = calc.calculate_liquidation_price(
        entry_price=entry_price,
        direction=direction,
        margin_rate=margin_rate,
        force_close_margin_rate=force_close_rate
    )

    # Calculate distance as percentage
    if direction == 'long':
        # For long: liquidation when price drops
        # Distance = (current - liquidation) / current
        distance_pct = ((current_price - liquidation_price) / current_price) * 100
    else:  # short
        # For short: liquidation when price rises
        # Distance = (liquidation - current) / current
        distance_pct = ((liquidation_price - current_price) / current_price) * 100

    logger.debug(
        f"{position.get('symbol', 'N/A')} ({direction}): Entry={entry_price}, "
        f"Current={current_price}, Liquidation={liquidation_price:.2f}, "
        f"Distance={distance_pct:.2f}%"
    )

    return distance_pct


def generate_liquidation_warnings(
    positions: List[Dict],
    current_prices: Dict[str, float],
    warning_threshold: float = 5.0,
    critical_threshold: float = 3.0
) -> List[Dict]:
    """Generate liquidation warnings for at-risk positions.

    Args:
        positions: List of futures positions
        current_prices: Dict of {symbol: price}
        warning_threshold: Yellow warning at this % distance (default 5%)
        critical_threshold: Red warning at this % distance (default 3%)

    Returns:
        List of warning dicts with:
        - symbol: str
        - distance_pct: float
        - liquidation_price: float
        - severity: 'critical' | 'warning'
        - message: str (Chinese)

    Example:
        >>> warnings = generate_liquidation_warnings(positions, prices)
        >>> # [{'symbol': 'IF2506', 'distance_pct': 2.5, 'severity': 'critical', ...}]
    """
    warnings = []

    for pos in positions:
        if pos.get('asset_type') != 'futures':
            continue

        symbol = pos['symbol']
        if symbol not in current_prices:
            logger.warning(f"No price available for {symbol}")
            continue

        current_price = current_prices[symbol]

        # Calculate distance to liquidation
        distance_pct = calculate_liquidation_distance(pos, current_price)

        # Generate warning if within threshold
        if distance_pct <= critical_threshold:
            # Critical warning (red)
            entry_price = pos.get('entry_price', 0)
            margin_rate = pos.get('margin_rate', 0.15)
            force_close_rate = pos.get('force_close_margin_rate', 0.03)

            from investlib_margin.calculator import MarginCalculator
            calc = MarginCalculator()
            liquidation_price = calc.calculate_liquidation_price(
                entry_price=entry_price,
                direction=pos.get('direction', 'long'),
                margin_rate=margin_rate,
                force_close_margin_rate=force_close_rate
            )

            warnings.append({
                'symbol': symbol,
                'distance_pct': distance_pct,
                'liquidation_price': liquidation_price,
                'current_price': current_price,
                'severity': 'critical',
                'message': f"⚠️ 强制平仓风险！{symbol} 距离平仓价仅 {distance_pct:.1f}%"
            })

        elif distance_pct <= warning_threshold:
            # Warning (yellow)
            entry_price = pos.get('entry_price', 0)
            margin_rate = pos.get('margin_rate', 0.15)
            force_close_rate = pos.get('force_close_margin_rate', 0.03)

            from investlib_margin.calculator import MarginCalculator
            calc = MarginCalculator()
            liquidation_price = calc.calculate_liquidation_price(
                entry_price=entry_price,
                direction=pos.get('direction', 'long'),
                margin_rate=margin_rate,
                force_close_margin_rate=force_close_rate
            )

            warnings.append({
                'symbol': symbol,
                'distance_pct': distance_pct,
                'liquidation_price': liquidation_price,
                'current_price': current_price,
                'severity': 'warning',
                'message': f"⚡ 注意！{symbol} 距离平仓价 {distance_pct:.1f}%"
            })

    # Sort by distance (most critical first)
    warnings.sort(key=lambda x: x['distance_pct'])

    if warnings:
        logger.warning(
            f"Generated {len(warnings)} liquidation warnings "
            f"({sum(1 for w in warnings if w['severity']=='critical')} critical)"
        )

    return warnings
