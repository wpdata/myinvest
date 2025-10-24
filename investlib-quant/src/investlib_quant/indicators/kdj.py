"""
KDJ Indicator (T062)

KDJ (Stochastic Oscillator) - momentum indicator for overbought/oversold conditions.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Literal
import logging


logger = logging.getLogger(__name__)


def calculate_kdj(
    df: pd.DataFrame,
    period: int = 9,
    k_smooth: int = 3,
    d_smooth: int = 3
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate KDJ indicator (Chinese Stochastic Oscillator).

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: RSV calculation period (default 9)
        k_smooth: K line smoothing period (default 3)
        d_smooth: D line smoothing period (default 3)

    Returns:
        Tuple of (k_line, d_line, j_line)
        - k_line: Fast stochastic (0-100)
        - d_line: Slow stochastic (0-100)
        - j_line: Divergence line (can exceed 0-100)

    Formula:
        RSV = (Close - Low_n) / (High_n - Low_n) * 100
        K = SMA(RSV, k_smooth)
        D = SMA(K, d_smooth)
        J = 3*K - 2*D

    Example:
        >>> k, d, j = calculate_kdj(df, period=9)
        >>> # Buy when K crosses above D in oversold zone (<20)
    """
    required_cols = ['high', 'low', 'close']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")

    # Calculate RSV (Raw Stochastic Value)
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()

    rsv = 100 * (df['close'] - low_min) / (high_max - low_min)
    rsv = rsv.fillna(50)  # Fill initial NaN with neutral 50

    # Calculate K line (SMA of RSV)
    k_line = rsv.ewm(span=k_smooth, adjust=False).mean()

    # Calculate D line (SMA of K)
    d_line = k_line.ewm(span=d_smooth, adjust=False).mean()

    # Calculate J line (3*K - 2*D)
    j_line = 3 * k_line - 2 * d_line

    logger.debug(
        f"Calculated KDJ (period={period}, k_smooth={k_smooth}, d_smooth={d_smooth})"
    )

    return k_line, d_line, j_line


def detect_kdj_signal(
    k_line: pd.Series,
    d_line: pd.Series,
    j_line: pd.Series,
    oversold_threshold: float = 20,
    overbought_threshold: float = 80
) -> Optional[Literal['buy', 'sell']]:
    """Detect KDJ trading signals.

    Args:
        k_line: K line values
        d_line: D line values
        j_line: J line values
        oversold_threshold: Oversold zone threshold (default 20)
        overbought_threshold: Overbought zone threshold (default 80)

    Returns:
        'buy' | 'sell' | None

    Signals:
        - buy: K crosses above D in oversold zone (< oversold_threshold)
        - sell: K crosses below D in overbought zone (> overbought_threshold)
        - None: No signal

    Example:
        >>> signal = detect_kdj_signal(k, d, j, oversold_threshold=20)
    """
    if len(k_line) < 2 or len(d_line) < 2:
        return None

    # Get current and previous values
    k_current = k_line.iloc[-1]
    k_previous = k_line.iloc[-2]
    d_current = d_line.iloc[-1]
    d_previous = d_line.iloc[-2]

    # Check for NaN
    if any(pd.isna([k_current, k_previous, d_current, d_previous])):
        return None

    # Buy signal: K crosses above D in oversold zone
    if (k_current > d_current and
        k_previous <= d_previous and
        k_current < oversold_threshold):
        logger.info(
            f"KDJ buy signal: K crossed above D in oversold zone "
            f"(K={k_current:.2f}, D={d_current:.2f})"
        )
        return 'buy'

    # Sell signal: K crosses below D in overbought zone
    elif (k_current < d_current and
          k_previous >= d_previous and
          k_current > overbought_threshold):
        logger.info(
            f"KDJ sell signal: K crossed below D in overbought zone "
            f"(K={k_current:.2f}, D={d_current:.2f})"
        )
        return 'sell'

    return None


def get_kdj_zone(
    k_line: pd.Series,
    d_line: pd.Series,
    oversold: float = 20,
    overbought: float = 80
) -> Literal['oversold', 'overbought', 'neutral']:
    """Determine current KDJ zone.

    Args:
        k_line: K line values
        d_line: D line values
        oversold: Oversold threshold (default 20)
        overbought: Overbought threshold (default 80)

    Returns:
        'oversold' | 'overbought' | 'neutral'

    Example:
        >>> zone = get_kdj_zone(k, d, oversold=20, overbought=80)
    """
    if len(k_line) == 0:
        return 'neutral'

    k_current = k_line.iloc[-1]

    if pd.isna(k_current):
        return 'neutral'

    if k_current < oversold:
        return 'oversold'
    elif k_current > overbought:
        return 'overbought'
    else:
        return 'neutral'


def detect_kdj_divergence(
    df: pd.DataFrame,
    k_line: pd.Series,
    lookback: int = 20
) -> Optional[Literal['bullish', 'bearish']]:
    """Detect KDJ divergence.

    Bullish: Price lower low, KDJ higher low (in oversold zone)
    Bearish: Price higher high, KDJ lower high (in overbought zone)

    Args:
        df: DataFrame with 'close' price
        k_line: K line values
        lookback: Periods to look back (default 20)

    Returns:
        'bullish' | 'bearish' | None

    Example:
        >>> divergence = detect_kdj_divergence(df, k_line, lookback=20)
    """
    if len(df) < lookback or len(k_line) < lookback:
        return None

    recent_price = df['close'].tail(lookback)
    recent_k = k_line.tail(lookback)

    # Find lows and highs
    price_low = recent_price.min()
    price_high = recent_price.max()
    k_low = recent_k.min()
    k_high = recent_k.max()

    current_price = recent_price.iloc[-1]
    current_k = recent_k.iloc[-1]

    # Bullish divergence: price lower low, K higher low (in oversold)
    if (current_price < price_low and
        current_k > k_low and
        current_k < 30):
        logger.info("KDJ bullish divergence detected")
        return 'bullish'

    # Bearish divergence: price higher high, K lower high (in overbought)
    if (current_price > price_high and
        current_k < k_high and
        current_k > 70):
        logger.info("KDJ bearish divergence detected")
        return 'bearish'

    return None


def get_kdj_strength(
    k_line: pd.Series,
    d_line: pd.Series,
    j_line: pd.Series
) -> dict:
    """Get KDJ signal strength.

    Args:
        k_line: K line
        d_line: D line
        j_line: J line

    Returns:
        Dict with:
        - momentum: 'strong_bullish' | 'bullish' | 'neutral' | 'bearish' | 'strong_bearish'
        - zone: 'oversold' | 'neutral' | 'overbought'
        - k_d_spread: K-D difference
        - j_extreme: Whether J line is in extreme territory

    Example:
        >>> strength = get_kdj_strength(k, d, j)
    """
    if len(j_line) == 0:
        return {'momentum': 'neutral', 'zone': 'neutral'}

    k_val = k_line.iloc[-1]
    d_val = d_line.iloc[-1]
    j_val = j_line.iloc[-1]

    k_d_spread = k_val - d_val

    # Determine zone
    if k_val < 20:
        zone = 'oversold'
    elif k_val > 80:
        zone = 'overbought'
    else:
        zone = 'neutral'

    # Determine momentum
    if k_d_spread > 10 and k_val > d_val:
        momentum = 'strong_bullish'
    elif k_d_spread > 0 and k_val > d_val:
        momentum = 'bullish'
    elif k_d_spread < -10 and k_val < d_val:
        momentum = 'strong_bearish'
    elif k_d_spread < 0 and k_val < d_val:
        momentum = 'bearish'
    else:
        momentum = 'neutral'

    # Check J line extremes
    j_extreme = j_val < 0 or j_val > 100

    return {
        'momentum': momentum,
        'zone': zone,
        'k_d_spread': float(k_d_spread),
        'j_extreme': j_extreme,
        'k_value': float(k_val),
        'd_value': float(d_val),
        'j_value': float(j_val)
    }


# Example usage
if __name__ == '__main__':
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Generate oscillating price
    base = 1900
    oscillation = 100 * np.sin(np.linspace(0, 4*np.pi, 100))
    noise = np.random.normal(0, 20, 100)
    close_prices = base + oscillation + noise

    df = pd.DataFrame({
        'timestamp': dates,
        'high': close_prices + np.abs(np.random.normal(10, 5, 100)),
        'low': close_prices - np.abs(np.random.normal(10, 5, 100)),
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, 100)
    })

    print("=" * 60)
    print("KDJ 指标测试")
    print("=" * 60)

    # Calculate KDJ
    k, d, j = calculate_kdj(df, period=9, k_smooth=3, d_smooth=3)

    print("\nKDJ 最近5天:")
    kdj_df = pd.DataFrame({
        'Date': df['timestamp'].tail(5),
        'Close': df['close'].tail(5),
        'K': k.tail(5),
        'D': d.tail(5),
        'J': j.tail(5)
    })
    print(kdj_df.to_string(index=False))

    # Detect signal
    signal = detect_kdj_signal(k, d, j, oversold_threshold=20, overbought_threshold=80)
    print(f"\n交易信号: {signal if signal else '无'}")

    # Get zone
    zone = get_kdj_zone(k, d, oversold=20, overbought=80)
    print(f"当前区域: {zone}")

    # Get strength
    strength = get_kdj_strength(k, d, j)
    print(f"\nKDJ 强度:")
    print(f"  动能: {strength['momentum']}")
    print(f"  区域: {strength['zone']}")
    print(f"  K-D差值: {strength['k_d_spread']:.2f}")
    print(f"  J线极值: {strength['j_extreme']}")
    print(f"  K值: {strength['k_value']:.2f}")
    print(f"  D值: {strength['d_value']:.2f}")
    print(f"  J值: {strength['j_value']:.2f}")

    # Detect divergence
    divergence = detect_kdj_divergence(df, k, lookback=30)
    print(f"\n背离信号: {divergence if divergence else '无'}")

    # Trading summary
    print("\n" + "=" * 60)
    print("交易建议")
    print("=" * 60)

    if signal == 'buy':
        print("✅ 买入信号 (K线上穿D线，超卖区)")
    elif signal == 'sell':
        print("❌ 卖出信号 (K线下穿D线，超买区)")
    elif zone == 'oversold':
        print("⚠️ 超卖区 (等待K线上穿D线)")
    elif zone == 'overbought':
        print("⚠️ 超买区 (等待K线下穿D线)")
    else:
        print("⏸️ 中性区域 (观望)")
