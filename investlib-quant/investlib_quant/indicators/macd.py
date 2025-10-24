"""
MACD Indicator (T061)

Moving Average Convergence Divergence - trend-following momentum indicator.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Literal
import logging


logger = logging.getLogger(__name__)


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    price_col: str = 'close'
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        df: DataFrame with price data
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)
        price_col: Column name for price (default 'close')

    Returns:
        Tuple of (macd_line, signal_line, histogram)
        - macd_line: DIF line (fast EMA - slow EMA)
        - signal_line: DEA line (signal EMA of MACD)
        - histogram: MACD - Signal (bar chart)

    Example:
        >>> macd, signal, hist = calculate_macd(df, fast=12, slow=26, signal=9)
        >>> # Bullish when MACD crosses above signal line
    """
    if price_col not in df.columns:
        raise ValueError(f"Column '{price_col}' not found in DataFrame")

    prices = df[price_col]

    # Calculate EMAs
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    # MACD line (DIF) = Fast EMA - Slow EMA
    macd_line = ema_fast - ema_slow

    # Signal line (DEA) = EMA of MACD line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # Histogram (MACD - Signal)
    histogram = macd_line - signal_line

    logger.debug(
        f"Calculated MACD (fast={fast}, slow={slow}, signal={signal}), "
        f"{macd_line.notna().sum()} valid values"
    )

    return macd_line, signal_line, histogram


def detect_macd_crossover(
    macd_line: pd.Series,
    signal_line: pd.Series
) -> Optional[Literal['bullish', 'bearish']]:
    """Detect MACD crossover signals.

    Args:
        macd_line: MACD DIF line
        signal_line: Signal DEA line

    Returns:
        'bullish' | 'bearish' | None

    Signals:
        - bullish: MACD crosses above signal line (golden cross)
        - bearish: MACD crosses below signal line (death cross)
        - None: No crossover

    Example:
        >>> signal = detect_macd_crossover(macd, signal_line)
        >>> if signal == 'bullish':
        ...     print("Buy signal!")
    """
    if len(macd_line) < 2 or len(signal_line) < 2:
        return None

    # Get latest and previous values
    macd_current = macd_line.iloc[-1]
    macd_previous = macd_line.iloc[-2]
    signal_current = signal_line.iloc[-1]
    signal_previous = signal_line.iloc[-2]

    # Check for NaN
    if any(pd.isna([macd_current, macd_previous, signal_current, signal_previous])):
        return None

    # Bullish crossover: MACD crosses above signal
    if macd_current > signal_current and macd_previous <= signal_previous:
        logger.info(
            f"MACD bullish crossover detected: "
            f"MACD={macd_current:.4f}, Signal={signal_current:.4f}"
        )
        return 'bullish'

    # Bearish crossover: MACD crosses below signal
    elif macd_current < signal_current and macd_previous >= signal_previous:
        logger.info(
            f"MACD bearish crossover detected: "
            f"MACD={macd_current:.4f}, Signal={signal_current:.4f}"
        )
        return 'bearish'

    return None


def detect_macd_divergence(
    df: pd.DataFrame,
    macd_line: pd.Series,
    lookback: int = 20
) -> Optional[Literal['bullish', 'bearish']]:
    """Detect MACD divergence (advanced signal).

    Bullish divergence: Price makes lower low, MACD makes higher low
    Bearish divergence: Price makes higher high, MACD makes lower high

    Args:
        df: DataFrame with 'close' price
        macd_line: MACD DIF line
        lookback: Number of periods to look back (default 20)

    Returns:
        'bullish' | 'bearish' | None

    Example:
        >>> divergence = detect_macd_divergence(df, macd_line, lookback=20)
    """
    if len(df) < lookback or len(macd_line) < lookback:
        return None

    recent_df = df.tail(lookback)
    recent_macd = macd_line.tail(lookback)

    # Find price highs and lows
    price_high = recent_df['close'].max()
    price_low = recent_df['close'].min()
    price_high_idx = recent_df['close'].idxmax()
    price_low_idx = recent_df['close'].idxmin()

    # Find MACD highs and lows
    macd_high = recent_macd.max()
    macd_low = recent_macd.min()
    macd_high_idx = recent_macd.idxmax()
    macd_low_idx = recent_macd.idxmin()

    current_price = recent_df['close'].iloc[-1]
    current_macd = recent_macd.iloc[-1]

    # Bullish divergence: price lower low, MACD higher low
    if (current_price < price_low and
        current_macd > macd_low and
        price_low_idx < len(recent_df) - 1):
        logger.info("MACD bullish divergence detected")
        return 'bullish'

    # Bearish divergence: price higher high, MACD lower high
    if (current_price > price_high and
        current_macd < macd_high and
        price_high_idx < len(recent_df) - 1):
        logger.info("MACD bearish divergence detected")
        return 'bearish'

    return None


def get_macd_strength(
    macd_line: pd.Series,
    signal_line: pd.Series,
    histogram: pd.Series
) -> dict:
    """Get MACD signal strength metrics.

    Args:
        macd_line: MACD DIF line
        signal_line: Signal DEA line
        histogram: Histogram

    Returns:
        Dict with strength metrics:
        - trend: 'bullish' | 'bearish' | 'neutral'
        - strength: 'strong' | 'moderate' | 'weak'
        - histogram_trend: 'expanding' | 'contracting'

    Example:
        >>> strength = get_macd_strength(macd, signal, hist)
        >>> print(strength['trend'], strength['strength'])
    """
    if len(histogram) < 3:
        return {'trend': 'neutral', 'strength': 'weak', 'histogram_trend': 'neutral'}

    latest_hist = histogram.iloc[-1]
    prev_hist = histogram.iloc[-2]

    # Determine trend
    if latest_hist > 0 and macd_line.iloc[-1] > signal_line.iloc[-1]:
        trend = 'bullish'
    elif latest_hist < 0 and macd_line.iloc[-1] < signal_line.iloc[-1]:
        trend = 'bearish'
    else:
        trend = 'neutral'

    # Determine strength based on histogram magnitude
    hist_abs = abs(latest_hist)
    hist_std = histogram.tail(20).std()

    if hist_abs > hist_std * 1.5:
        strength = 'strong'
    elif hist_abs > hist_std * 0.5:
        strength = 'moderate'
    else:
        strength = 'weak'

    # Determine histogram trend
    if abs(latest_hist) > abs(prev_hist):
        histogram_trend = 'expanding'
    else:
        histogram_trend = 'contracting'

    return {
        'trend': trend,
        'strength': strength,
        'histogram_trend': histogram_trend,
        'histogram_value': float(latest_hist)
    }


# Example usage
if __name__ == '__main__':
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
    np.random.seed(42)

    # Generate trending price with oscillation
    trend = np.linspace(1800, 2000, 200)
    cycle = 50 * np.sin(np.linspace(0, 4*np.pi, 200))
    noise = np.random.normal(0, 15, 200)
    close_prices = trend + cycle + noise

    df = pd.DataFrame({
        'timestamp': dates,
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, 200)
    })

    print("=" * 60)
    print("MACD 指标测试")
    print("=" * 60)

    # Calculate MACD
    macd, signal, hist = calculate_macd(df, fast=12, slow=26, signal=9)

    print("\nMACD 最近5天:")
    macd_df = pd.DataFrame({
        'Date': df['timestamp'].tail(5),
        'Close': df['close'].tail(5),
        'MACD': macd.tail(5),
        'Signal': signal.tail(5),
        'Histogram': hist.tail(5)
    })
    print(macd_df.to_string(index=False))

    # Detect crossover
    crossover = detect_macd_crossover(macd, signal)
    print(f"\n交叉信号: {crossover if crossover else '无'}")

    # Get strength
    strength = get_macd_strength(macd, signal, hist)
    print(f"\nMACD 强度:")
    print(f"  趋势: {strength['trend']}")
    print(f"  强度: {strength['strength']}")
    print(f"  柱状图趋势: {strength['histogram_trend']}")
    print(f"  柱状图值: {strength['histogram_value']:.4f}")

    # Detect divergence
    divergence = detect_macd_divergence(df, macd, lookback=30)
    print(f"\n背离信号: {divergence if divergence else '无'}")

    # Trading signal summary
    print("\n" + "=" * 60)
    print("交易信号总结")
    print("=" * 60)

    if crossover == 'bullish':
        print("✅ 买入信号 (MACD金叉)")
    elif crossover == 'bearish':
        print("❌ 卖出信号 (MACD死叉)")
    elif divergence == 'bullish':
        print("🔄 潜在买入 (看涨背离)")
    elif divergence == 'bearish':
        print("🔄 潜在卖出 (看跌背离)")
    else:
        print("⏸️ 观望 (无明确信号)")
