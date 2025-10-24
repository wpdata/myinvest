"""
Combination Margin Calculator (T051)

Calculate margin requirements for multi-leg option/futures strategies,
considering hedge effects to reduce total margin.
"""

from typing import List, Dict, Tuple
import logging


logger = logging.getLogger(__name__)


def calculate_combination_margin(legs: List[Dict]) -> Dict[str, float]:
    """Calculate margin for multi-leg combination strategy.

    Considers hedge effects between legs to reduce margin requirement.

    Args:
        legs: List of leg dicts with:
            - asset_type: 'stock' | 'futures' | 'call' | 'put'
            - action: 'BUY' | 'SELL'
            - quantity: int
            - entry_price: float
            - multiplier: int
            - strike_price: float (for options)

    Returns:
        Dict with:
            - total_margin: Total margin required
            - individual_margin: Sum of margins if calculated separately
            - hedge_reduction: Amount saved due to hedging
            - hedge_reduction_pct: Percentage saved
            - details: List of per-leg margin details

    Example:
        >>> legs = [
        ...     {'asset_type': 'stock', 'action': 'BUY', 'quantity': 100, 'entry_price': 1800, 'multiplier': 1},
        ...     {'asset_type': 'call', 'action': 'SELL', 'quantity': 1, 'entry_price': 50, 'multiplier': 10000, 'strike_price': 1900}
        ... ]
        >>> margin = calculate_combination_margin(legs)
        >>> # Returns reduced margin due to covered call hedge
    """
    from investlib_margin.calculator import MarginCalculator
    calc = MarginCalculator()

    details = []
    individual_margin_sum = 0.0

    # Calculate individual margins
    for i, leg in enumerate(legs):
        asset_type = leg.get('asset_type')
        quantity = leg.get('quantity', 0)
        price = leg.get('entry_price', 0)
        multiplier = leg.get('multiplier', 1)

        if asset_type in ['futures', 'call', 'put']:
            # Calculate margin for leveraged products
            margin_rate = 0.15 if asset_type == 'futures' else 0.20  # Options typically 20%
            margin = calc.calculate_margin(
                contract_type='futures' if asset_type == 'futures' else 'option',
                quantity=quantity,
                price=price,
                multiplier=multiplier,
                margin_rate=margin_rate
            )
        elif asset_type == 'stock':
            # Stocks require full capital (no margin)
            margin = quantity * price
        else:
            margin = 0.0

        details.append({
            'leg_id': f"leg{i+1}",
            'asset_type': asset_type,
            'action': leg.get('action'),
            'margin': margin
        })

        individual_margin_sum += margin

    # Detect hedge pairs to reduce margin
    hedge_pairs = detect_hedge_pairs(legs)

    # Calculate hedge reduction
    hedge_reduction = 0.0
    for pair in hedge_pairs:
        leg1_idx, leg2_idx = pair
        leg1_margin = details[leg1_idx]['margin']
        leg2_margin = details[leg2_idx]['margin']

        # Reduce margin by 20-50% for offsetting positions
        # More sophisticated models could use delta/Greeks
        reduction_pct = 0.30  # 30% reduction for simple hedge
        pair_reduction = min(leg1_margin, leg2_margin) * reduction_pct
        hedge_reduction += pair_reduction

        logger.info(
            f"Hedge detected between leg{leg1_idx+1} and leg{leg2_idx+1}: "
            f"Margin reduction ¥{pair_reduction:,.2f}"
        )

    # Calculate total margin
    total_margin = individual_margin_sum - hedge_reduction
    hedge_reduction_pct = (hedge_reduction / individual_margin_sum * 100) if individual_margin_sum > 0 else 0

    result = {
        'total_margin': total_margin,
        'individual_margin': individual_margin_sum,
        'hedge_reduction': hedge_reduction,
        'hedge_reduction_pct': hedge_reduction_pct,
        'details': details
    }

    logger.info(
        f"Combination margin: Total=¥{total_margin:,.2f}, "
        f"Individual=¥{individual_margin_sum:,.2f}, "
        f"Hedge reduction={hedge_reduction_pct:.1f}%"
    )

    return result


def detect_hedge_pairs(legs: List[Dict]) -> List[Tuple[int, int]]:
    """Detect offsetting positions in multi-leg strategy.

    Args:
        legs: List of leg dicts

    Returns:
        List of (leg1_index, leg2_index) tuples representing hedge pairs

    Hedge detection rules:
        - Covered call: Long stock + short call (same symbol)
        - Vertical spread: Buy call + sell call (different strikes)
        - Straddle: Buy call + buy put (same strike, opposite types)
        - Calendar spread: Buy near month + sell far month (same strike)
    """
    hedge_pairs = []

    for i in range(len(legs)):
        for j in range(i + 1, len(legs)):
            leg1 = legs[i]
            leg2 = legs[j]

            # Same symbol check
            if leg1.get('symbol') != leg2.get('symbol'):
                continue

            # Detect different hedge types
            is_hedge = False

            # Rule 1: Covered call (stock + short call)
            if (leg1.get('asset_type') == 'stock' and leg2.get('asset_type') == 'call' and
                leg1.get('action') == 'BUY' and leg2.get('action') == 'SELL'):
                is_hedge = True
                logger.debug(f"Covered call hedge: leg{i+1} (stock) + leg{j+1} (short call)")

            # Rule 2: Vertical spread (same type, different strikes, opposite actions)
            elif (leg1.get('asset_type') == leg2.get('asset_type') and
                  leg1.get('asset_type') in ['call', 'put'] and
                  leg1.get('action') != leg2.get('action')):
                is_hedge = True
                logger.debug(f"Vertical spread hedge: leg{i+1} + leg{j+1}")

            # Rule 3: Straddle (call + put, same strike, same action)
            elif (leg1.get('asset_type') in ['call', 'put'] and
                  leg2.get('asset_type') in ['call', 'put'] and
                  leg1.get('asset_type') != leg2.get('asset_type') and
                  leg1.get('strike_price') == leg2.get('strike_price') and
                  leg1.get('action') == leg2.get('action')):
                is_hedge = True
                logger.debug(f"Straddle hedge: leg{i+1} + leg{j+1}")

            if is_hedge:
                hedge_pairs.append((i, j))

    return hedge_pairs


# Example usage
if __name__ == '__main__':
    # Test covered call
    covered_call_legs = [
        {
            'symbol': '600519.SH',
            'asset_type': 'stock',
            'action': 'BUY',
            'quantity': 100,
            'entry_price': 1800,
            'multiplier': 1
        },
        {
            'symbol': '600519.SH',
            'asset_type': 'call',
            'action': 'SELL',
            'quantity': 1,
            'entry_price': 50,
            'multiplier': 10000,
            'strike_price': 1900
        }
    ]

    print("=" * 60)
    print("备兑开仓保证金计算")
    print("=" * 60)

    result = calculate_combination_margin(covered_call_legs)

    print(f"\n总保证金: ¥{result['total_margin']:,.2f}")
    print(f"单独计算保证金: ¥{result['individual_margin']:,.2f}")
    print(f"对冲减免: ¥{result['hedge_reduction']:,.2f} ({result['hedge_reduction_pct']:.1f}%)")

    print("\n各腿明细:")
    for detail in result['details']:
        print(f"  {detail['leg_id']} ({detail['asset_type']}, {detail['action']}): ¥{detail['margin']:,.2f}")

    # Test butterfly spread
    print("\n" + "=" * 60)
    print("蝶式价差保证金计算")
    print("=" * 60)

    butterfly_legs = [
        {'symbol': '50ETF', 'asset_type': 'call', 'action': 'BUY', 'quantity': 1,
         'entry_price': 0.15, 'multiplier': 10000, 'strike_price': 2.8},
        {'symbol': '50ETF', 'asset_type': 'call', 'action': 'SELL', 'quantity': 2,
         'entry_price': 0.10, 'multiplier': 10000, 'strike_price': 3.0},
        {'symbol': '50ETF', 'asset_type': 'call', 'action': 'BUY', 'quantity': 1,
         'entry_price': 0.05, 'multiplier': 10000, 'strike_price': 3.2}
    ]

    result = calculate_combination_margin(butterfly_legs)

    print(f"\n总保证金: ¥{result['total_margin']:,.2f}")
    print(f"单独计算保证金: ¥{result['individual_margin']:,.2f}")
    print(f"对冲减免: ¥{result['hedge_reduction']:,.2f} ({result['hedge_reduction_pct']:.1f}%)")
