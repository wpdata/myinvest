"""
Combination Strategy P&L Chart Generator (T053)

Generate profit/loss charts for multi-leg option strategies.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import logging


logger = logging.getLogger(__name__)


def calculate_combination_pnl(
    legs: List[Dict],
    underlying_prices: np.ndarray
) -> pd.DataFrame:
    """Calculate P&L across a range of underlying prices.

    Args:
        legs: List of leg dicts with:
            - asset_type: 'stock' | 'call' | 'put'
            - action: 'BUY' | 'SELL'
            - quantity: int
            - entry_price: float
            - strike_price: float (for options)
            - multiplier: int
        underlying_prices: Array of prices to evaluate

    Returns:
        DataFrame with columns:
            - price: Underlying price
            - pnl: Total P&L at this price
            - pnl_per_leg: Dict of per-leg P&L

    Example:
        >>> legs = [
        ...     {'asset_type': 'stock', 'action': 'BUY', 'quantity': 100, 'entry_price': 1800, 'multiplier': 1},
        ...     {'asset_type': 'call', 'action': 'SELL', 'quantity': 1, 'entry_price': 50, 'strike_price': 1900, 'multiplier': 10000}
        ... ]
        >>> prices = np.linspace(1600, 2000, 100)
        >>> pnl_df = calculate_combination_pnl(legs, prices)
    """
    results = []

    for price in underlying_prices:
        total_pnl = 0.0
        leg_pnls = {}

        for i, leg in enumerate(legs):
            leg_pnl = calculate_leg_pnl_at_price(leg, price)
            total_pnl += leg_pnl
            leg_pnls[f"leg{i+1}"] = leg_pnl

        results.append({
            'price': price,
            'pnl': total_pnl,
            'pnl_per_leg': leg_pnls
        })

    return pd.DataFrame(results)


def calculate_leg_pnl_at_price(leg: Dict, underlying_price: float) -> float:
    """Calculate P&L for a single leg at a given underlying price.

    Args:
        leg: Leg dict
        underlying_price: Current underlying price

    Returns:
        P&L for this leg (positive = profit, negative = loss)
    """
    asset_type = leg.get('asset_type')
    action = leg.get('action')
    quantity = leg.get('quantity', 1)
    entry_price = leg.get('entry_price', 0)
    strike_price = leg.get('strike_price', 0)
    multiplier = leg.get('multiplier', 1)

    direction = 1 if action == 'BUY' else -1

    if asset_type == 'stock':
        # Stock P&L = (current_price - entry_price) * quantity * direction
        pnl = (underlying_price - entry_price) * quantity * direction

    elif asset_type == 'call':
        # Call option intrinsic value
        intrinsic_value = max(0, underlying_price - strike_price)

        if action == 'BUY':
            # Long call: Profit = (intrinsic - premium) * quantity * multiplier
            pnl = (intrinsic_value - entry_price) * quantity * multiplier
        else:
            # Short call: Profit = (premium - intrinsic) * quantity * multiplier
            pnl = (entry_price - intrinsic_value) * quantity * multiplier

    elif asset_type == 'put':
        # Put option intrinsic value
        intrinsic_value = max(0, strike_price - underlying_price)

        if action == 'BUY':
            # Long put: Profit = (intrinsic - premium) * quantity * multiplier
            pnl = (intrinsic_value - entry_price) * quantity * multiplier
        else:
            # Short put: Profit = (premium - intrinsic) * quantity * multiplier
            pnl = (entry_price - intrinsic_value) * quantity * multiplier

    else:
        pnl = 0.0

    return pnl


def find_breakeven_points(pnl_df: pd.DataFrame) -> List[float]:
    """Find breakeven prices where P&L crosses zero.

    Args:
        pnl_df: DataFrame from calculate_combination_pnl()

    Returns:
        List of breakeven prices (where pnl ≈ 0)
    """
    breakevens = []

    for i in range(len(pnl_df) - 1):
        pnl_current = pnl_df.iloc[i]['pnl']
        pnl_next = pnl_df.iloc[i + 1]['pnl']

        # Check if sign changes (crosses zero)
        if pnl_current * pnl_next < 0:
            # Interpolate to find exact breakeven
            price_current = pnl_df.iloc[i]['price']
            price_next = pnl_df.iloc[i + 1]['price']

            # Linear interpolation
            breakeven = price_current - pnl_current * (price_next - price_current) / (pnl_next - pnl_current)
            breakevens.append(breakeven)

    return breakevens


def calculate_max_profit_loss(pnl_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate max profit and max loss from P&L curve.

    Args:
        pnl_df: DataFrame from calculate_combination_pnl()

    Returns:
        Dict with:
            - max_profit: Maximum possible profit
            - max_profit_at: Price where max profit occurs
            - max_loss: Maximum possible loss
            - max_loss_at: Price where max loss occurs
    """
    max_pnl = pnl_df['pnl'].max()
    min_pnl = pnl_df['pnl'].min()

    max_profit_row = pnl_df.loc[pnl_df['pnl'].idxmax()]
    max_loss_row = pnl_df.loc[pnl_df['pnl'].idxmin()]

    return {
        'max_profit': max_pnl,
        'max_profit_at': max_profit_row['price'],
        'max_loss': min_pnl,
        'max_loss_at': max_loss_row['price']
    }


def generate_pnl_plot_data(
    legs: List[Dict],
    underlying_price_range: Tuple[float, float] = None,
    num_points: int = 200
) -> Dict:
    """Generate complete P&L plot data for visualization.

    Args:
        legs: List of leg dicts
        underlying_price_range: (min_price, max_price) or None (auto-detect)
        num_points: Number of points to calculate

    Returns:
        Dict with:
            - pnl_df: DataFrame with P&L data
            - breakeven_points: List of breakeven prices
            - max_profit_loss: Dict with max profit/loss info
            - current_price: Current/ATM price (estimated)
    """
    # Auto-detect price range if not provided
    if underlying_price_range is None:
        strikes = [leg.get('strike_price', 0) for leg in legs if leg.get('strike_price')]
        if strikes:
            min_strike = min(strikes)
            max_strike = max(strikes)
            price_range = max_strike - min_strike
            underlying_price_range = (
                min_strike - price_range * 0.2,
                max_strike + price_range * 0.2
            )
        else:
            # Default range if no strikes
            underlying_price_range = (1000, 2000)

    # Generate price array
    prices = np.linspace(underlying_price_range[0], underlying_price_range[1], num_points)

    # Calculate P&L
    pnl_df = calculate_combination_pnl(legs, prices)

    # Find breakevens
    breakeven_points = find_breakeven_points(pnl_df)

    # Calculate max profit/loss
    max_profit_loss = calculate_max_profit_loss(pnl_df)

    # Estimate current price (mid-point of strikes or range)
    strikes = [leg.get('strike_price', 0) for leg in legs if leg.get('strike_price')]
    current_price = sum(strikes) / len(strikes) if strikes else np.mean(underlying_price_range)

    logger.info(
        f"P&L plot generated: {num_points} points, "
        f"{len(breakeven_points)} breakevens, "
        f"Max profit=¥{max_profit_loss['max_profit']:,.2f}, "
        f"Max loss=¥{max_profit_loss['max_loss']:,.2f}"
    )

    return {
        'pnl_df': pnl_df,
        'breakeven_points': breakeven_points,
        'max_profit_loss': max_profit_loss,
        'current_price': current_price,
        'price_range': underlying_price_range
    }


# Example usage
if __name__ == '__main__':
    # Test covered call
    covered_call_legs = [
        {
            'asset_type': 'stock',
            'action': 'BUY',
            'quantity': 100,
            'entry_price': 1800,
            'multiplier': 1
        },
        {
            'asset_type': 'call',
            'action': 'SELL',
            'quantity': 1,
            'entry_price': 50,
            'strike_price': 1900,
            'multiplier': 10000
        }
    ]

    print("=" * 60)
    print("备兑开仓 P&L 分析")
    print("=" * 60)

    plot_data = generate_pnl_plot_data(
        covered_call_legs,
        underlying_price_range=(1600, 2000),
        num_points=100
    )

    print(f"\n价格区间: ¥{plot_data['price_range'][0]:.0f} - ¥{plot_data['price_range'][1]:.0f}")
    print(f"当前价格（估计）: ¥{plot_data['current_price']:.2f}")

    print(f"\n盈亏平衡点:")
    for i, bp in enumerate(plot_data['breakeven_points'], 1):
        print(f"  盈亏平衡点 {i}: ¥{bp:.2f}")

    max_pnl = plot_data['max_profit_loss']
    print(f"\n最大盈利: ¥{max_pnl['max_profit']:,.2f} (在 ¥{max_pnl['max_profit_at']:.2f})")
    print(f"最大亏损: ¥{max_pnl['max_loss']:,.2f} (在 ¥{max_pnl['max_loss_at']:.2f})")

    # Show sample P&L at key prices
    print("\n关键价格点的 P&L:")
    pnl_df = plot_data['pnl_df']
    for price in [1700, 1800, 1900, 2000]:
        row = pnl_df.iloc[(pnl_df['price'] - price).abs().argmin()]
        print(f"  ¥{row['price']:.0f}: P&L = ¥{row['pnl']:,.2f}")
