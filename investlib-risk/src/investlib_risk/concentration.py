"""Concentration risk analysis.

Identifies over-concentration in single positions or industries.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


def calculate_concentration(positions: List[Dict]) -> Dict[str, float]:
    """Calculate position concentration metrics.

    Args:
        positions: List of position dicts with 'symbol' and 'value' keys

    Returns:
        Dict with concentration metrics:
        - max_single_position_pct: Largest single position as % of portfolio
        - top3_concentration_pct: Top 3 positions as % of portfolio
        - herfindahl_index: Herfindahl-Hirschman Index (0-1, lower is more diversified)
        - total_positions: Number of positions

    Example:
        >>> positions = [
        ...     {'symbol': '600519.SH', 'value': 50000},
        ...     {'symbol': '000001.SZ', 'value': 30000},
        ...     {'symbol': '000858.SZ', 'value': 20000}
        ... ]
        >>> metrics = calculate_concentration(positions)
        >>> # {'max_single_position_pct': 50.0, ...}
    """
    if not positions:
        logger.warning("No positions provided")
        return {
            'max_single_position_pct': 0.0,
            'top3_concentration_pct': 0.0,
            'herfindahl_index': 0.0,
            'total_positions': 0
        }

    # Calculate total value
    total_value = sum(pos.get('value', 0) for pos in positions)

    if total_value == 0:
        logger.warning("Total portfolio value is 0")
        return {
            'max_single_position_pct': 0.0,
            'top3_concentration_pct': 0.0,
            'herfindahl_index': 0.0,
            'total_positions': len(positions)
        }

    # Calculate position percentages
    position_pcts = []
    for pos in positions:
        value = pos.get('value', 0)
        pct = (value / total_value) * 100
        position_pcts.append({
            'symbol': pos['symbol'],
            'value': value,
            'pct': pct
        })

    # Sort by percentage (descending)
    position_pcts.sort(key=lambda x: x['pct'], reverse=True)

    # Max single position
    max_single_pct = position_pcts[0]['pct'] if position_pcts else 0.0

    # Top 3 concentration
    top3_pct = sum(pos['pct'] for pos in position_pcts[:3])

    # Herfindahl-Hirschman Index (HHI)
    # HHI = sum of squared market shares (0 to 1 scale)
    hhi = sum((pos['pct'] / 100) ** 2 for pos in position_pcts)

    metrics = {
        'max_single_position_pct': max_single_pct,
        'top3_concentration_pct': top3_pct,
        'herfindahl_index': hhi,
        'total_positions': len(positions)
    }

    logger.info(
        f"Concentration metrics: Max={max_single_pct:.1f}%, "
        f"Top3={top3_pct:.1f}%, HHI={hhi:.3f}, Positions={len(positions)}"
    )

    return metrics


def calculate_industry_concentration(
    positions: List[Dict],
    industry_map: Optional[Dict[str, str]] = None
) -> Dict[str, float]:
    """Calculate industry-level concentration.

    Args:
        positions: List of position dicts with 'symbol' and 'value'
        industry_map: Dict mapping symbol to industry (e.g., {'600519.SH': 'Consumer', ...})

    Returns:
        Dict of {industry: percentage} sorted by concentration

    Example:
        >>> positions = [
        ...     {'symbol': '600519.SH', 'value': 50000},
        ...     {'symbol': '600036.SH', 'value': 30000}
        ... ]
        >>> industry_map = {'600519.SH': '白酒', '600036.SH': '银行'}
        >>> concentration = calculate_industry_concentration(positions, industry_map)
        >>> # {'白酒': 50.0, '银行': 30.0, '未分类': 20.0}
    """
    if not positions:
        logger.warning("No positions provided")
        return {}

    # Use provided industry map or default to "未分类" (uncategorized)
    industry_map = industry_map or {}

    # Calculate total value
    total_value = sum(pos.get('value', 0) for pos in positions)

    if total_value == 0:
        logger.warning("Total portfolio value is 0")
        return {}

    # Aggregate by industry
    industry_values = {}
    for pos in positions:
        symbol = pos['symbol']
        value = pos.get('value', 0)
        industry = industry_map.get(symbol, '未分类')

        if industry not in industry_values:
            industry_values[industry] = 0.0
        industry_values[industry] += value

    # Convert to percentages
    industry_pcts = {
        industry: (value / total_value) * 100
        for industry, value in industry_values.items()
    }

    # Sort by concentration (descending)
    sorted_pcts = dict(
        sorted(industry_pcts.items(), key=lambda x: x[1], reverse=True)
    )

    logger.info(
        f"Industry concentration: {len(sorted_pcts)} industries, "
        f"Max={max(sorted_pcts.values()):.1f}%"
    )

    return sorted_pcts
