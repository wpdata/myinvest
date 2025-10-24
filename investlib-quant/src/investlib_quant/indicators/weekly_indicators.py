"""
Weekly Indicator Calculator (T058)

Calculate technical indicators on weekly timeframe data.
"""

import pandas as pd
import numpy as np
from typing import Literal, Optional, Tuple
import logging


logger = logging.getLogger(__name__)


def calculate_weekly_ma(
    weekly_df: pd.DataFrame,
    period: int = 20
) -> pd.Series:
    """Calculate moving average on weekly data.

    Args:
        weekly_df: Weekly DataFrame with 'close' column
        period: MA period (default 20 weeks ≈ 5 months)

    Returns:
        Series of MA values

    Example:
        >>> weekly_ma = calculate_weekly_ma(weekly_data, period=20)
    """
    if 'close' not in weekly_df.columns:
        raise ValueError("DataFrame must have 'close' column")

    ma = weekly_df['close'].rolling(window=period).mean()

    logger.debug(f"Calculated {period}-week MA, {ma.notna().sum()} valid values")

    return ma


def calculate_weekly_macd(
    weekly_df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD on weekly data.

    Args:
        weekly_df: Weekly DataFrame with 'close' column
        fast: Fast EMA period (default 12 weeks)
        slow: Slow EMA period (default 26 weeks)
        signal: Signal line period (default 9 weeks)

    Returns:
        Tuple of (macd_line, signal_line, histogram)

    Example:
        >>> macd, signal, hist = calculate_weekly_macd(weekly_data)
    """
    if 'close' not in weekly_df.columns:
        raise ValueError("DataFrame must have 'close' column")

    # Calculate EMAs
    ema_fast = weekly_df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = weekly_df['close'].ewm(span=slow, adjust=False).mean()

    # MACD line = Fast EMA - Slow EMA
    macd_line = ema_fast - ema_slow

    # Signal line = EMA of MACD line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # Histogram = MACD - Signal
    histogram = macd_line - signal_line

    logger.debug(
        f"Calculated weekly MACD (fast={fast}, slow={slow}, signal={signal})"
    )

    return macd_line, signal_line, histogram


def detect_weekly_trend(
    weekly_df: pd.DataFrame,
    ma_short: int = 10,
    ma_long: int = 20
) -> Literal['up', 'down', 'sideways']:
    """Detect weekly trend based on moving averages.

    Args:
        weekly_df: Weekly DataFrame
        ma_short: Short MA period (default 10 weeks)
        ma_long: Long MA period (default 20 weeks)

    Returns:
        'up' | 'down' | 'sideways'

    Logic:
        - up: short MA > long MA and price > short MA
        - down: short MA < long MA and price < short MA
        - sideways: otherwise

    Example:
        >>> trend = detect_weekly_trend(weekly_data)
        >>> # Returns 'up', 'down', or 'sideways'
    """
    if weekly_df.empty or len(weekly_df) < ma_long:
        logger.warning(f"Insufficient data for trend detection (need {ma_long} weeks)")
        return 'sideways'

    # Calculate MAs
    ma_s = calculate_weekly_ma(weekly_df, period=ma_short)
    ma_l = calculate_weekly_ma(weekly_df, period=ma_long)

    # Get latest values
    latest_price = weekly_df.iloc[-1]['close']
    latest_ma_short = ma_s.iloc[-1]
    latest_ma_long = ma_l.iloc[-1]

    # Check for NaN
    if pd.isna(latest_ma_short) or pd.isna(latest_ma_long):
        return 'sideways'

    # Detect trend
    if latest_ma_short > latest_ma_long and latest_price > latest_ma_short:
        trend = 'up'
    elif latest_ma_short < latest_ma_long and latest_price < latest_ma_short:
        trend = 'down'
    else:
        trend = 'sideways'

    logger.info(
        f"Weekly trend: {trend.upper()} "
        f"(Price={latest_price:.2f}, MA{ma_short}={latest_ma_short:.2f}, "
        f"MA{ma_long}={latest_ma_long:.2f})"
    )

    return trend


def calculate_weekly_rsi(
    weekly_df: pd.DataFrame,
    period: int = 14
) -> pd.Series:
    """Calculate RSI on weekly data.

    Args:
        weekly_df: Weekly DataFrame with 'close' column
        period: RSI period (default 14 weeks)

    Returns:
        Series of RSI values (0-100)

    Example:
        >>> weekly_rsi = calculate_weekly_rsi(weekly_data, period=14)
    """
    if 'close' not in weekly_df.columns:
        raise ValueError("DataFrame must have 'close' column")

    # Calculate price changes
    delta = weekly_df['close'].diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    logger.debug(f"Calculated {period}-week RSI")

    return rsi


def detect_weekly_support_resistance(
    weekly_df: pd.DataFrame,
    lookback: int = 52  # 1 year of weeks
) -> Tuple[float, float]:
    """Detect weekly support and resistance levels.

    Args:
        weekly_df: Weekly DataFrame
        lookback: Number of weeks to look back (default 52 = 1 year)

    Returns:
        Tuple of (support_level, resistance_level)

    Example:
        >>> support, resistance = detect_weekly_support_resistance(weekly_data)
    """
    if weekly_df.empty or len(weekly_df) < lookback:
        logger.warning(f"Insufficient data for S/R detection (need {lookback} weeks)")
        recent_data = weekly_df
    else:
        recent_data = weekly_df.tail(lookback)

    # Support: lowest low in period
    support = recent_data['low'].min()

    # Resistance: highest high in period
    resistance = recent_data['high'].max()

    logger.info(
        f"Weekly S/R levels: Support={support:.2f}, Resistance={resistance:.2f}"
    )

    return support, resistance


def calculate_weekly_volatility(
    weekly_df: pd.DataFrame,
    period: int = 20
) -> float:
    """Calculate annualized volatility from weekly returns.

    Args:
        weekly_df: Weekly DataFrame
        period: Number of weeks for calculation (default 20)

    Returns:
        Annualized volatility (percentage)

    Example:
        >>> vol = calculate_weekly_volatility(weekly_data)
        >>> # Returns annualized volatility in %
    """
    if weekly_df.empty or len(weekly_df) < period + 1:
        logger.warning("Insufficient data for volatility calculation")
        return 0.0

    # Calculate weekly returns
    returns = weekly_df['close'].pct_change()

    # Get recent returns
    recent_returns = returns.tail(period)

    # Calculate standard deviation
    weekly_std = recent_returns.std()

    # Annualize (52 weeks per year)
    annualized_vol = weekly_std * np.sqrt(52) * 100

    logger.info(f"Weekly volatility (annualized): {annualized_vol:.2f}%")

    return annualized_vol


# Example usage
if __name__ == '__main__':
    # Create sample weekly data
    from investlib_data.resample import resample_to_weekly

    # Generate daily data first
    dates = pd.date_range(start='2023-01-01', end='2025-01-31', freq='D')
    np.random.seed(42)

    trend = np.linspace(1800, 2000, len(dates))
    noise = np.random.normal(0, 30, len(dates))
    close_prices = trend + noise

    daily_data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.normal(0, 5, len(dates)),
        'high': close_prices + np.abs(np.random.normal(15, 5, len(dates))),
        'low': close_prices - np.abs(np.random.normal(15, 5, len(dates))),
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, len(dates))
    })

    # Convert to weekly
    weekly_data = resample_to_weekly(daily_data)

    print("=" * 60)
    print("周线指标计算测试")
    print("=" * 60)

    # Calculate weekly MA
    weekly_ma20 = calculate_weekly_ma(weekly_data, period=20)
    print(f"\n20周均线 (最近5周):")
    print(weekly_ma20.tail(5))

    # Calculate weekly MACD
    macd, signal, hist = calculate_weekly_macd(weekly_data)
    print(f"\n周线MACD (最近5周):")
    macd_df = pd.DataFrame({
        'MACD': macd,
        'Signal': signal,
        'Histogram': hist
    })
    print(macd_df.tail(5))

    # Detect weekly trend
    trend = detect_weekly_trend(weekly_data, ma_short=10, ma_long=20)
    print(f"\n周线趋势: {trend.upper()}")

    # Calculate weekly RSI
    weekly_rsi = calculate_weekly_rsi(weekly_data, period=14)
    print(f"\n14周RSI (最近5周):")
    print(weekly_rsi.tail(5))

    # Detect S/R levels
    support, resistance = detect_weekly_support_resistance(weekly_data, lookback=52)
    print(f"\n周线支撑/阻力:")
    print(f"  支撑位: ¥{support:.2f}")
    print(f"  阻力位: ¥{resistance:.2f}")

    # Calculate volatility
    vol = calculate_weekly_volatility(weekly_data, period=20)
    print(f"\n周线波动率 (年化): {vol:.2f}%")
